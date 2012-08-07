import logging

from boto.exception import S3ResponseError
from cliff.command import Command
from cliff.show import ShowOne

from brainstorm.main import parse_path
from brainstorm.main import parse_acl


class DeleteObjects(Command):
    """Delete an existing object
    """

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(DeleteObjects, self).get_parser(prog_name)
        parser.add_argument('objects', nargs='+', type=parse_path,
            help='list of objects to delete')
        parser.add_argument('-b', '--bucket',
            help='bucket to delete objects from')
        return parser

    def take_action(self, parsed_args):
        for bucketname, keyname in parsed_args.objects:
            if bucketname and not keyname:
                # something like -b mybucket object1
                keyname = bucketname
                bucketname = parsed_args.bucket
            if not bucketname:
                # something like -b mybucket :object1
                bucketname = parsed_args.bucket
            bucket = self.app.conn.lookup(bucketname)
            if bucket:
                self.log.debug('looking up key %s in bucket %s'
                        % (keyname, bucketname))
                k = bucket.get_key(keyname)
                if k:
                    try:
                        self.log.debug('deleting key %s' % keyname)
                        k.delete()
                    except S3ResponseError:
                        self.log.warn('could not remove key %s' % keyname)
                else:
                    self.log.warn('could not load key %s' % keyname)
            else:
                self.log.warn('could not load bucket %s' % bucketname)


class ShowObject(ShowOne):
    """Show information about an object
    """

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(ShowObject, self).get_parser(prog_name)
        parser.add_argument('object', type=parse_path,
            help='name of object to show like bucket:object')
        return parser

    def take_action(self, parsed_args):
        bucketname, keyname = parsed_args.object
        bucket = self.app.conn.lookup(bucketname)
        if bucket:
            self.log.debug('looking up key %s in bucket %s'
                    % (keyname, bucketname))
            k = bucket.get_key(keyname)
            if k:
                rows = ['Name', 'Size', 'Last Modified', 'Content Type',
                        'etag', 'ACLs']
                data = [k.name, k.size, k.last_modified, k.content_type,
                        k.etag, '']
                acp = k.get_acl()
                for (entity, permissions) in parse_acl(acp):
                    rows.append('  %s' % entity)
                    data.append(permissions)
                if k.metadata:
                    rows.append('Metadata')
                    data.append('')
                    for x, v in k.metadata.iteritems():
                        rows.append('  %s' % x)
                        data.append(v)

                return (rows, data)
            else:
                self.log.warn('could not load key %s in bucket %s'
                        % (keyname, bucketname))
        else:
            self.log.warn('could not load bucket %s' % bucketname)
