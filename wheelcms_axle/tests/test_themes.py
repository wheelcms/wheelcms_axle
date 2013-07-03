from wheelcms_axle.configuration import ConfigurationForm

class TestThemes(object):
    def test_themes_form_choices(self):
        f = ConfigurationForm()
        assert ('default', 'Bootstrap') in f.fields['theme'].choices
