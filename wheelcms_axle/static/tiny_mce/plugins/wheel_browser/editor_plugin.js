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
                var dom = ed.dom;
                var anchor = dom.getParent(ed.selection.getNode(), 'A');
                var href = "";
                var options = {};

                if(anchor) {
                    href = dom.getAttrib(anchor, 'href');
                    options.title = dom.getAttrib(anchor, 'title');
                    options.target = dom.getAttrib(anchor, 'target');
                    if(href.match(/\+download$/)) {
                        options.download = true;
                        href = href.replace(/\/\+download$/, '');
                    }
                }

                ed.getWin().parent.props_or_browser(href, "link", options,
                                                 function(link, options) {
                    href = href.replace(/ /g, '%20');
                    if(anchor == null) {
                        /* messy way to insert a link .. */
                        var marker = "#wheel_temp_url#";
                        ed.execCommand("mceInsertLink", false, marker, {skip_undo : 1});
                        var elementArray = tinymce.grep(dom.select("a"),
                                   function(n) {
                                         return dom.getAttrib(n, 'href') == marker;
                                   });
                        anchor = elementArray[0]; // expect one, only one
                    }
                    if(options.download) {
                        if(!/\/$/.test(link)) {
                            link += '/';
                        }
                        link += "/+download";
                    }
                    dom.setAttrib(anchor, 'href', link);
                    if(options.title) {
                        dom.setAttrib(anchor, 'title', options.title);
                    }
                    if(options.target) {
                        dom.setAttrib(anchor, 'target', options.target);
                    }
                });
            });
            ed.addCommand('wheelImage', function() {
                var node = ed.selection.getNode();

                var src = "";
                var title = "";
                var options = {};

                if(node.nodeName=="IMG") {
                    src = ed.dom.getAttrib(node, 'src');
                    options.title = ed.dom.getAttrib(node, 'alt') || ed.dom.getAttrib(node, 'title');
                    options.klass = ed.dom.getAttrib(node, 'class') || '';
                }

                ed.getWin().parent.props_or_browser(src, "image", options,
                                                 function(link, options) {
                    // Fixes crash in Safari
                    if (tinymce.isWebKit) {
                        ed.getWin().focus();
                    }
                    var args = {src:link, "class":""};
                    if(options.local) {
                        if(!/\/$/.test(args.src)) {
                            args.src += '/';
                        }
                        args.src += '+download';
                    }
                    if(options.title) {
                        args.title = options.title;
                        args.alt = options.title;
                    }
                    // should probably be configurable
                    args['class'] = "img-polaroid ";
                    args['class'] += (options.size || 'original');
                    args['class'] += " " + (options.float || "");
                    args['class'] += " " + (options.align || "");

                    ed.execCommand('mceInsertContent', false,
                                   ed.dom.createHTML('img', args),
                                   {skip_undo : 1});
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
