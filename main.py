import os
import cgi
import datetime
import urllib
import wsgiref.handlers
import re
import httplib
import json

from google.appengine.ext.webapp import template
from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

class AuthenticatedPage(webapp.RequestHandler):
    pass

######################## Helpers ##########################
def getTranslationFromQQ(self, wordlist):
    httpServ = httplib.HTTPConnection("dict.qq.com", 80)
    httpServ.connect()
    
    for wordElement in wordlist:
        wordKey = db.Key.from_path("Word", wordElement["name"])
        wordRecord = db.get(wordKey)
        if wordRecord:
            wordElement["meaning"] = wordRecord.translation
            continue
        
        # TODO: coroutine optimisation
        httpServ.request('GET', "/dict?q=" + wordElement["name"])

        response = httpServ.getresponse()
        if response.status == httplib.OK:
            data = json.load(response)
            try:
                des = data["local"][0]["des"]
                ds = [" ".join([value for key, value in ele.iteritems()]) 
                        for ele in des]
                wordElement["meaning"] = "; ".join(ds)
                wordRecord = Word(key_name=wordElement["name"], 
                                    translation = wordElement["meaning"],
                                    origine = repr(response))
                wordRecord.put()
                                    
            except KeyError:
                pass
            pass
        pass
    return wordlist

######################## Decorators ##########################

def requireLogin(f):
    def wrapper(self, *args, **kwargs):
        # TODO: check how users are used?
        user = users.get_current_user()

        if user:
            
            # TODO: this maight introduce a bug:
            # if a class has various methods which requires diff auth cond
            # some of them may have self.user some of them not..
            # should check when classes are inited.
            self.user = user
            f(self, *args, **kwargs)
        else:
            self.redirect(users.create_login_url(self.request.uri))
        pass
    return wrapper

def templateFile(filename, filepath=__file__):
    # TODO: filepath as input should be count reference to __file__
    def wrapperParameters(f):
        def wrapperMethod(self, *args, **kwargs):
            var = f(self, *args, **kwargs)
            path = os.path.join(os.path.dirname(filepath), filename)
            self.response.out.write(template.render(path, var))
            pass
        return wrapperMethod
        pass
    return wrapperParameters

######################## Model ##########################

class Profile(db.Model):
    # Entity is named by property id or name 
    name = db.StringProperty()
    wordlist = db.StringListProperty()

    @staticmethod
    def getProfileOfUser(user):
        userProfileKey = db.Key.from_path("Profile", user.email())
        userProfile = None
        try:
            userProfile = db.get(userProfileKey)
        except NotSavedError:
            pass
        finally:
            if userProfile == None:
                userProfile = Profile(key_name=user.email(), 
                                        name=user.nickname(), wordlist=[])
                userProfile.put()
                pass
            pass
        return userProfile

class Word(db.Model):
    name = db.StringListProperty()
    translation = db.StringProperty(multiline=True)        
    origine = db.StringProperty(multiline=True)
            
class Article(db.Model):
    title = db.StringProperty()
    content = db.StringProperty(multiline=True)

######################## Controller ##########################

class MainPage(AuthenticatedPage):
    @requireLogin
    @templateFile("home.html")
    def get(self):
        pass

class NewArticlePage(AuthenticatedPage):
    @requireLogin
    @templateFile("new.html")
    def post(self):
        # unique, no seperator, no word of len 1 ('s after seperate)
        profile = Profile.getProfileOfUser(self.user)

        content = self.request.get("content")
        # maight consider seperator in unicode plus - issue
        words = re.split(r"[ .\"\'\n\t:;,?!~|()\[\]#+=%\\/><]+", content)
        words = filter(lambda x: len(x)>1, words)
        # an article related to map performance: (str.lower bad for unicode)
        # http://stackoverflow.com/questions/1247486/python-list-comprehension-vs-map
        words = map(lambda x: x.lower().strip(), words)
        oldWords = set(words).intersection( set(profile.wordlist) )
        newWords = set(words) - set(oldWords)

        profile.wordlist = list(newWords | set(profile.wordlist))
        profile.put()

        wordlist = [dict(id=idx, name=val, meaning="unkown")
                            for idx, val in enumerate(newWords)]
        wordlist = getTranslationFromQQ(self, wordlist)
        
        return {"newWords": wordlist, "content": content}
        pass

class WordsPage(AuthenticatedPage):
    @requireLogin
    @templateFile("words.html")
    def get(self):
        profile = Profile.getProfileOfUser(self.user)
        learntWords = profile.wordlist
        return {"words": learntWords}
        pass

class ArticlesPage(AuthenticatedPage):
    @requireLogin
    @templateFile("articles.html")
    def get(self):
        article1 = {"title": "Title1", "content": "Content1"}
        article2 = {"title": "Title2", "content": "Content2"}
        articles = [article1, article2]
        return {"articles": articles}
        pass

application = webapp.WSGIApplication(
                     [('/', MainPage),
				      ('/new', NewArticlePage),
				      ('/words', WordsPage),
				      ('/articles', ArticlesPage)],
                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
