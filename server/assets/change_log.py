from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from .models import App, ChangeLog

models = ['XRefProperty', 'Vulnerability', 'Asset', 'IPAddress', 'MACAddress', 'Host', 'App', 'Port', 'Site']


def log_change(model, id, deleted=False):
    print(model, id, deleted)
    change = ChangeLog()
    change.model = model
    change.uid = id
    change.deleted = deleted
    change.save()


def save_delete_handler(sender, **kwargs):
    instance = kwargs.get('instance')
    if not instance: return
    model = type(instance).__name__
    if model not in models: return
    log_change(model, instance.pk, kwargs.get('deleted'))


@receiver(post_save)
def save_handler(sender, **kwargs):
    kwargs['deleted'] = False
    save_delete_handler(sender, **kwargs)


@receiver(post_delete)
def delete_handler(sender, **kwargs):
    kwargs['deleted'] = True
    save_delete_handler(sender, **kwargs)


@receiver(m2m_changed)
def m2m_handler(sender, **kwargs):
    if kwargs.get('action') in ['post_add', 'post_remove']:
        kwargs['deleted'] = False
        save_delete_handler(sender, **kwargs)
        for id in (kwargs.get('pk_set') or []):
            log_change(kwargs['model'].__name__, id)

