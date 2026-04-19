from django.db import migrations, models
import django.db.models.deletion


def create_compot_users(apps, schema_editor):
    Member = apps.get_model('pots', 'Member')
    CompotUser = apps.get_model('pots', 'CompotUser')
    for member in Member.objects.all():
        user, _ = CompotUser.objects.get_or_create(
            telegram_user_id=member.telegram_user_id,
            defaults={
                'name': member.name,
                'telegram_username': member.telegram_username,
            },
        )
        member.user = user
        member.save(update_fields=['user'])


class Migration(migrations.Migration):

    dependencies = [
        ('pots', '0004_drop_time'),
    ]

    operations = [
        migrations.CreateModel(
            name='CompotUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('telegram_user_id', models.BigIntegerField(blank=True, null=True, unique=True)),
                ('name', models.CharField(max_length=100)),
                ('telegram_username', models.CharField(blank=True, max_length=100)),
            ],
        ),
        migrations.AddField(
            model_name='member',
            name='user',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='memberships',
                to='pots.compotuser',
            ),
        ),
        migrations.RunPython(create_compot_users, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='member',
            name='user',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='memberships',
                to='pots.compotuser',
            ),
        ),
        migrations.AlterUniqueTogether(
            name='member',
            unique_together=set(),
        ),
        migrations.RemoveField(model_name='member', name='telegram_user_id'),
        migrations.RemoveField(model_name='member', name='name'),
        migrations.RemoveField(model_name='member', name='telegram_username'),
        migrations.AlterUniqueTogether(
            name='member',
            unique_together={('pot', 'user')},
        ),
    ]
