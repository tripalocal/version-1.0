class message_router(object):

    def db_for_read(self, model, **hints):
        #with open('app_label', 'a') as f:
        #    f.write(model._meta.app_label + "\n")
        #    f.close()

        if model._meta.app_label == 'tripalocal_messages':           
            return 'maildb'
        #elif model._meta.app_label == 'experiences':
        #    return 'experiencedb'
        return None
 
    def db_for_write(self, model, **hints):
        if model._meta.app_label == 'tripalocal_messages':
            return 'maildb'
        #elif model._meta.app_label == 'experiences':
        #    return 'experiencedb'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        "Allow any relation if a both models in tripalocal_messages app"
        if obj1._meta.app_label == 'tripalocal_messages' and obj2._meta.app_label == 'tripalocal_messages':
            return True
        if obj1._meta.app_label == 'experiences' and obj2._meta.app_label == 'experiences':
            return True
        if obj1._meta.app_label == 'app' and obj2._meta.app_label == 'app':
            return True
        if obj1._meta.app_label == 'app' and obj2._meta.app_label == 'experiences':
            return True
        if obj1._meta.app_label == 'experiences' and obj2._meta.app_label == 'app':
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

        #if db == 'experiencedb':
        #    return model._meta.app_label == 'experiences'
        #elif model._meta.app_label == 'experiences':
        #    return False

        return None
