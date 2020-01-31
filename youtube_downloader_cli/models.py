from peewee import *
from playhouse.sqlite_ext import *
from os.path import exists, join
from enum import IntFlag
from .config import get_storage_path, DATABASE_FILE
from .translate import translate2chinese as translate

# http://docs.peewee-orm.com/en/latest/peewee/database.html#run-time-database-configuration
_db_proxy = DatabaseProxy()

class VideoPlatformFlag(IntFlag):
    'All kinds of platform flags.'
    Acfun = 1 << 0
    Bilibili = 1 << 1
    Youtube = 1 << 2


class PeeweeModel(Model):
    class Meta:
        database = _db_proxy

    @classmethod
    def initialize(cls, data):
        'Generic initializer.'
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

    filename = CharField(null=True)
    total_bytes = BigIntegerField(null=True, default=0)

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
        item.uploader = Uploader.initialize(data)

        item.save()
        return item

    def check_for_upload(self, flag):
        'Check condition for upload.'

        def check_existence(file):
            return file and exists(join(get_storage_path(), file))

        if not check_existence(self.thumbnail):
            return False, 'Invalid video thumbnail!'

        if not check_existence(self.filename):
            return False, 'Invalid video file!'

        return True, None

    def localized_title(self):
        return translate(self.title)

    def localized_tags(self):
        return list(map(translate, self.tags))

    def localized_categories(self):
        return list(map(translate, self.categories))

    def localized_description(self):
        return translate(self.description)

def setup_database(dbpath):
    '''Initialize database.'''

    database = SqliteDatabase(dbpath)
    _db_proxy.initialize(database)

    database.connect(reuse_if_open=True)
    database.create_tables([
        Uploader,
        Playlist,
        Video,
    ])

    return database
