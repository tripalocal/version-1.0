class message_router(object):

    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'tripalocal_messages':
            return 'maildb'
        return None
 
    def db_for_write(self, model, **hints):
        if model._meta.app_label == 'tripalocal_messages':
            return 'maildb'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        "Allow any relation if a both models in tripalocal_messages app"
        if obj1._meta.app_label == 'tripalocal_messages' and obj2._meta.app_label == 'tripalocal_messages':
            return True
        return None
 
    def allow_syncdb(self, db, model):
        """
        Make sure the 'tripalocal_messages' app only appears on the 'other' db
        """
        if db == 'maildb':
            return model._meta.app_label == 'tripalocal_messages'
        elif model._meta.app_label == 'tripalocal_messages':
            return False
        return None
