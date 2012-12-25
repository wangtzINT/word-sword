from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

class MainPage(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()

        if user:
            self.response.headers['Content-Type'] = 'text/plain'
            self.response.out.write('Hello, ' + user.nickname())
        else:
            self.redirect(users.create_login_url(self.request.uri))

class NewArticlePage(webapp.RequestHandler):
    def post(self):
	pass

class WordsPage(webapp.RequestHandler):
    def get(self):
	pass

class ArticlesPage(webapp.RequestHandler):
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
