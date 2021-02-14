
import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from sqlalchemy import Column, Integer, String

from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

import wormnest.utils as utils
# import  utils

engine = create_engine('sqlite:///url.db', echo=False)
Session = sessionmaker(bind=engine)

class Url(Base):
	__tablename__ = 'urls'

	# id = Column(Integer, )
	url_alias = Column(String, nullable=False, primary_key=True)
	path = Column(String, nullable=False)
	expires_after_clicks = Column(Integer, default = -1)
	attachment = Column(String)
	mimetype = Column(String, nullable=True, default=None)

	def __repr__(self):
		return "(URL: /{} for file '{}'. Expires in {} requests. {})".format(
			self.url_alias,
			self.path,
			self.expires_after_clicks,
			"Served as '%s'." % self.attachment if self.attachment else '',
			)

Base.metadata.create_all(engine)


def get_all(path=None):
	session = Session()
	if path is None:
		return session.query(Url).all()	
	return session.query(Url).filter(Url.path.ilike(path)).all()


def get_path(alias, click=True, delete=False):
	session = Session()
	try:
		entry = session.query(Url).filter(Url.url_alias == alias).one()
	except sqlalchemy.orm.exc.NoResultFound as e:
		entry = None

	if entry is None:
		session.close()
		raise KeyError("Entry not available for '{}'".format(alias))

	print (entry)
	if delete:
		session.delete(entry)
		session.commit()
		return True

	if not click:
		session.close()
		return entry

	if entry.expires_after_clicks == -1:
		session.close()
		return entry

	if entry.expires_after_clicks > 0:
		entry.expires_after_clicks -= 1
		session.commit()
		return entry

	raise utils.LinkExpired("Link {} expired".format(entry.url_alias))



def add_url(path, url_alias, expires, attachment=None, mimetype=None):
	session = Session()
	entry = Url(
		path=path,
		url_alias=url_alias,
		expires_after_clicks=expires,
		attachment = attachment,
		mimetype = mimetype
		)
	session.add(entry)
	session.commit()



def del_url(url_alias):

	return get_path(url_alias, click=False, delete=True)

