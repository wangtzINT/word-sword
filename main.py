import os
from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

class AuthenticatedPage(webapp.RequestHandler):
    pass

def requireLogin(f):
    def wrapper(self, *args, **kwargs):
        # TODO: check how users are used?
        user = users.get_current_user()

        if user:
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
        

class MainPage(AuthenticatedPage):
    @requireLogin
    @templateFile("home.html")
    def get(self):
        pass

class NewArticlePage(AuthenticatedPage):
    @requireLogin
    @templateFile("new.html")
    def post(self):
        words = self.request.get("content").split("[ \S.;,?!~|()\[\]{}'\"")
        newWords = ["new", "worlds"]
        oldWords = ["old", "mots"]
        return {"oldWords": oldWords, "newWords": newWords}
        pass

class WordsPage(AuthenticatedPage):
    @requireLogin
    @templateFile("words.html")
    def get(self):
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
