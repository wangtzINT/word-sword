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
            self.response.headers['Content-Type'] = 'text/plain'
            f(self, *args, **kwargs)
        else:
            self.redirect(users.create_login_url(self.request.uri))
        pass
    return wrapper

class MainPage(AuthenticatedPage):
    @requireLogin
    def get(self):
        pass

class NewArticlePage(AuthenticatedPage):
    @requireLogin
    def getWord(self):
        pass

class WordsPage(AuthenticatedPage):
    @requireLogin
    def get(self):
        pass

class ArticlesPage(AuthenticatedPage):
    @requireLogin
    def get(self):
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
