(function() {
    tinymce.create('wheelcms.plugins.WheelBrowser', {
        init: function(ed, url) {
            ed.addButton('link', {
                title: 'Add/edit link',
                cmd: 'wheelLink',
                image: ''
            });
            ed.addCommand('wheelLink', function() {
                var anchor = ed.dom.getParent(ed.selection.getNode(), 'A');
                var href = "";
                var title = "";

                if(anchor) {
			        href = ed.dom.getAttrib(anchor, 'href');
			        title = ed.dom.getAttrib(anchor, 'title');
                    console.log("Selection : " + href + ", " + title);
                }

                ed.getWin().parent.wheel_browser(href, function(link) {
                    ed.formatter.apply('link', {'href':link}, anchor);
                });
            });
        },
        getInfo: function() {
            return {
                longname: 'WheelCMS browser popup',
                author: 'Ivo van der Wijk',
                authorurl: 'http://vanderwijk.info',
                infourl: 'http://vanderwijk.info',
                version: '1.0'
            };
        }
    });
    tinymce.PluginManager.add('wheel_browser', wheelcms.plugins.WheelBrowser);
})();
