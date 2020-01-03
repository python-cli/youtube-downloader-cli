from peewee import *
from playhouse.sqlite_ext import *
from .config import pretty_json_string, DATABASE_FILE
from .logger import getLogger

_db = SqliteDatabase(DATABASE_FILE)
logger = getLogger(__name__)


class PeeweeModel(Model):
    class Meta:
        database = _db

    @classmethod
    def initialize(cls, data):
        assert(isinstance(data, dict))

class Uploader(PeeweeModel):
    id = CharField(primary_key=True)
    name = CharField(null=True)
    url = CharField(null=True)

    def __str__(self):
        return 'id: %s, url: %s' % (self.id, self.name)

    @classmethod
    def initialize(cls, data):
        super(Uploader, cls).initialize(data)

        if not data.get('uploader_id'):
            return None

        item, _ = cls.get_or_create(id=data.get('uploader_id'))
        item.name = data.get('uploader')
        item.url = data.get('uploader_url')

        item.save()
        return item

class Playlist(PeeweeModel):
    id = CharField(primary_key=True)
    title = CharField(null=True)
    webpage_url = CharField(null=True)
    uploader = ForeignKeyField(Uploader, backref='videos', null=True)

    def __str__(self):
        return 'id: %s, title: %s' % (self.id, self.title)

    @classmethod
    def initialize(cls, data):
        super(Playlist, cls).initialize(data)

        item, _ = cls.get_or_create(id=data.get('id'))
        item.title = data.get('title')
        item.webpage_url = data.get('webpage_url')
        item.uploader = Uploader.initialize(data)

        item.save()
        return item

class Video(PeeweeModel):
    id = CharField(primary_key=True)
    title = CharField(null=True)
    url = CharField(null=True)
    webpage_url = CharField(null=True)

    duration = IntegerField(null=True)
    width = IntegerField(null=True)
    height = IntegerField(null=True)
    fps = IntegerField(null=True)
    ext = CharField(null=True)
    view_count = IntegerField(null=True)
    like_count = IntegerField(null=True)
    average_rating = DoubleField(null=True)

    channel_id = CharField(null=True)
    channel_url = CharField(null=True)
    upload_date = CharField(null=True)
    thumbnail = CharField(null=True)
    description = CharField(null=True)
    categories = JSONField(null=True)
    tags = JSONField(null=True)
    description = CharField(null=True)

    filename = CharField(null=True)
    total_bytes = BigIntegerField(null=True, default=0)
    upload_flags = BigIntegerField(null=True, default=0)

    uploader = ForeignKeyField(Uploader, backref='videos', null=True)
    playlist = ForeignKeyField(Playlist, backref='videos', null=True)

    def __str__(self):
        return 'id: %s, title: %s' % (self.id, self.title)

    @classmethod
    def initialize(cls, data):
        super(Video, cls).initialize(data)

        item, _ = cls.get_or_create(id=data.get('id'))
        item.title = data.get('title')
        item.webpage_url = data.get('webpage_url')
        item.duration = data.get('duration')
        item.width = data.get('width')
        item.height = data.get('height')
        item.fps = data.get('fps')
        item.ext = data.get('ext')
        item.view_count = data.get('view_count')
        item.like_count = data.get('like_count')
        item.average_rating = data.get('average_rating')
        item.channel_id = data.get('channel_id')
        item.channel_url = data.get('channel_url')
        item.upload_date = data.get('upload_date')
        item.thumbnail = data.get('thumbnail')
        item.description = data.get('description')
        item.categories = data.get('categories')
        item.tags = data.get('tags')
        item.description = data.get('description')
        item.uploader = Uploader.initialize(data)

        item.save()
        return item

_db.connect()
_db.create_tables([
    Uploader,
    Playlist,
    Video,
])
