__author__ = 'lyy'

from experiences.models import *

experinece_list = Experience.objects.all()
for exp in experinece_list:
    exp_id = exp.id
    for title in ExperienceTitle.objects.all():
        if title.experience_id == exp_id:
            exp_i18n = ExperienceI18n()
            exp_i18n.experience_id = exp_id
            exp_i18n.title = title.title
            exp_i18n.language = title.language
            exp_description_list = ExperienceDescription.objects.filter(experience_id=exp_id, language=title.language)
            if exp_description_list.__len__() == 1:
                exp_i18n.description = exp_description_list[0].description
            exp_activity_list = ExperienceActivity.objects.filter(experience_id=exp_id, language=title.language)
            if exp_activity_list.__len__() == 1:
                exp_i18n.activity = exp_activity_list[0].activity
            exp_interaction_list = ExperienceInteraction.objects.filter(experience_id=exp_id, language=title.language)
            if exp_interaction_list.__len__() == 1:
                exp_i18n.interaction = exp_interaction_list[0].interaction
            exp_dress_list = ExperienceDress.objects.filter(experience_id=exp_id, language=title.language)
            if exp_dress_list.__len__() == 1:
                exp_i18n.dress = exp_dress_list[0].dress
            exp_meetup_spot_list = ExperienceMeetupSpot.objects.filter(experience_id=exp_id, language=title.language)
            if exp_meetup_spot_list.__len__() == 1:
                exp_i18n.meetup_spot = exp_meetup_spot_list[0].meetup_spot
            exp_dropoff_spot_list = ExperienceDropoffSpot.objects.filter(experience_id=exp_id, language=title.language)
            if exp_dropoff_spot_list.__len__() == 1:
                exp_i18n.dropoff_spot = exp_dropoff_spot_list[0].dropoff_spot
            exp_i18n.save()
