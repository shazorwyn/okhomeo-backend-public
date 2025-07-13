# store/signals.py

from django.db.models.signals import post_save, post_delete, pre_delete
from django.contrib.contenttypes.models import ContentType
from django.db.utils import ProgrammingError, OperationalError
from django.conf import settings
from django.db.models import ProtectedError
from django.dispatch import receiver
import logging
from .models import Product, Cart


def connect_content_object_signals():
    def create_handler(model_class):
        def handler(sender, instance, **kwargs):
            try:
                ct = ContentType.objects.get_for_model(sender)
                product = Product.objects.get(content_type=ct, object_id=instance.id)
                product.save()
            except Product.DoesNotExist:
                pass
            except (ProgrammingError, OperationalError) as e:
                logging.warning(f"Skipped signal connection, DB not ready yet: {e}")

        return handler

    try:
        for ct in Product.get_allowed_content_types():
            model = ct.model_class()
            handler = create_handler(model)
            post_save.connect(handler, sender=model, weak=False)
    except (ProgrammingError, OperationalError) as e:
        logging.warning(f"Skipped signal connection, DB not ready yet: {e}")


@receiver(post_delete, sender=Cart)
def create_cart_after_deletion(sender, instance, **kwargs):
    user = instance.user
    if user and not Cart.objects.filter(user=user).exists():
        Cart.objects.create(user=user)


@receiver(pre_delete)
def prevent_deletion_if_product_exists(sender, instance, **kwargs):
    content_type = ContentType.objects.get_for_model(sender)
    if Product.objects.filter(
        content_type=content_type, object_id=instance.pk
    ).exists():
        raise ProtectedError(
            f"Cannot delete {sender.__name__} object {instance.pk} because it is referenced by a Product.",
            [instance],
        )
