# vim: set fileencoding=utf-8 :
import os
import cgi
import datetime
import urllib
import wsgiref.handlers
import re
import httplib
import json
import logging
from extension.stardict import IfoFileReader, IdxFileReader, DictFileReader
from xml.dom import minidom

from google.appengine.ext.webapp import template
from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

class AuthenticatedPage(webapp.RequestHandler):
    pass

######################## Helpers ##########################
class Seperator(object):
    def getWordList(self, content):
        # maight consider seperator in unicode plus - issue
        words = re.split(r"[ .\"\'\n\t:;,?!~|()\[\]#+=%\\/><0-9]+", content)
        # avoid empty string etc
        words = filter(lambda x: len(x)>1, words)
        # an article related to map performance: (str.lower bad for unicode)
        # http://stackoverflow.com/questions/1247486/python-list-comprehension-vs-map
        words = map(lambda x: x.lower().strip(), words)
        return words
    
class Translator(object):
    def __init__(self):
        # star dict part
        self.ifo_file = "dict/powerword2007_pwqec.ifo"
        self.idx_file = "dict/powerword2007_pwqec.idx"
        self.dict_file = "dict/powerword2007_pwqec.dict.dz"
        self.ifo_reader = IfoFileReader(self.ifo_file)
        self.idx_reader = IdxFileReader(self.idx_file)
        # TODO: This dict is too big to be entirely loaded (about 110M)
        # which force me to use F2 frontend instance
        # need to find a way to reduce its usage
        # !AND! speed up the lauch time!
        
        # TODO: this reader is not thread-safe, need to create
        # multiple instances, one for each thread
        self.dict_reader = DictFileReader(self.dict_file, 
                                            self.ifo_reader, 
                                            self.idx_reader, 
                                            True)
        # qq translation
        self.httpServ = httplib.HTTPConnection("dict.qq.com", 80, timeout=10)
        self.httpServ.connect()
        pass
    
    def run(self, wordlist):
        for wordElement in wordlist:
            wordElement["meaning"] = self.getMeaning(wordElement["name"])
        return wordlist
    
    def getMeaning(self, wordName):
        meaning = self.getTranslationFromDB(wordName)
        if meaning: return meaning
        meaning = self.getTranslationFromStarDict(wordName)
        if meaning: return meaning
        meaning = self.getTranslationFromQQ(wordName)
        if meaning: return meaning
        meaning = "unknown"
        self.storeTranslationToDB(wordName, meaning, None)
        return meaning
    
    def storeTranslationToDB(self, wordName, meaning, response):
        wordRecord = Word(key_name=wordName, 
                            translation = meaning,
                            origine = repr(response))
        wordRecord.put()
    
    def getTranslationFromDB(self, wordName):
        wordKey = db.Key.from_path("Word", wordName)
        wordRecord = db.get(wordKey)
        if wordRecord:
            return wordRecord.translation
        else:
            return None

    def getTranslationFromStarDict(self, wordName):
        raw = self.dict_reader.get_dict_by_word(wordName)
        if raw:
            xmldoc = minidom.parseString(raw[0]["k"])
            categories = xmldoc.getElementsByTagName(u"单词词性")
            meanings = xmldoc.getElementsByTagName(u"解释项")
            commonLen = min(len(categories), len(meanings))
            translation = "; ".join([
                        " ".join([categories[i].firstChild.wholeText,
                                    meanings[i].firstChild.wholeText])
                        for i in range(commonLen)
                        ])
        else:
            translation = None
        return translation
        pass

    def getTranslationFromQQ(self, wordName):
        # TODO: coroutine optimisation
        self.httpServ.request('GET', "/dict?q=" + wordName)
        response = self.httpServ.getresponse()
        if response.status == httplib.OK:
            data = json.load(response)
            try:
                des = data["local"][0]["des"]
                ds = [" ".join([value for key, value in ele.iteritems()]) 
                        for ele in des]
                meaning = "; ".join(ds)
                self.storeTranslationToDB(wordName, meaning, response)
                return meaning
            except KeyError:
                pass
            pass
        return None
        pass

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
        words = seperator.getWordList(content)

        oldWords = set(words).intersection( set(profile.wordlist) )
        newWords = set(words) - set(oldWords)

        profile.wordlist = list(newWords | set(profile.wordlist))
        profile.put()

        wordlist = [dict(id=idx, name=val, meaning="unkown")
                            for idx, val in enumerate(newWords)]
        wordlist = translator.run(wordlist) 
        
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

class RemoveWordAction(AuthenticatedPage):
    @requireLogin
    def post(self):
        uselessWords = seperator.getWordList(self.request.get("term"))
        profile = Profile.getProfileOfUser(self.user)
        learntWords = set(profile.wordlist) - set(uselessWords)
        profile.wordlist = list(learntWords)
        profile.put()
        response = {"status": "successed"}
        self.response.out.write(json.dumps(response))
        pass

class AddWordAction(AuthenticatedPage):
    @requireLogin
    def post(self):
        uselessWords = seperator.getWordList(self.request.get("term"))
        profile = Profile.getProfileOfUser(self.user)
        learntWords = set(profile.wordlist).union( set(uselessWords) )
        profile.wordlist = list(learntWords)
        profile.put()
        response = {"status": "successed"}
        self.response.out.write(json.dumps(response))
        pass

class CountWordAction(AuthenticatedPage):
    @requireLogin
    def post(self):
        profile = Profile.getProfileOfUser(self.user)
        count = len(profile.wordlist)
        response = {"count": repr(count)}
        self.response.out.write(json.dumps(response))
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
				      ('/article/new', NewArticlePage),
				      ('/article/list', ArticlesPage),
                      ('/word/add', AddWordAction),
                      ('/word/remove', RemoveWordAction),
				      ('/word/list', WordsPage),
                      ('/word/count', CountWordAction)],
                     debug=True)
translator = Translator()
seperator = Seperator()

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
