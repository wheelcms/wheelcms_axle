(function() {
    tinymce.create('wheelcms.plugins.WheelBrowser', {
        init: function(ed, url) {
            ed.addButton('link', {
                title: 'Add/edit link',
                cmd: 'wheelLink',
                image: ''
            });
            ed.addButton('image', {
                title: 'Add/edit image',
                cmd: 'wheelImage',
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

                ed.getWin().parent.wheel_browser(href, "link",
                                                 function(link) {
                    ed.formatter.apply('link', {'href':link}, anchor);
                });
            });
            ed.addCommand('wheelImage', function() {
                var node = ed.selection.getNode();

                var src = "";
                var title = "";

                if(node.nodeName=="IMG") {
                    src = ed.dom.getAttrib(node, 'src');
                    // get other attribs
                    //title = ed.dom.getAttrib(anchor, 'title');
                    console.log("Selection : " + src);
                }

                ed.getWin().parent.wheel_browser(src, "image",
                                                 function(link) {
                    // Fixes crash in Safari
                    if (tinymce.isWebKit) {
                        ed.getWin().focus();
                    }
                    var args = {src:link + '/download'};
                    ed.execCommand('mceInsertContent', false, ed.dom.createHTML('img', args), {skip_undo : 1});
                    ed.undoManager.add();

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
