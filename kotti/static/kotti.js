// JSLint options:
/*global deform, jQuery, tinyMCE*/
/*jslint browser:true*/

"use strict";
var kotti = {
    domChangedHandlers: []
};
var jq = jQuery;

(function ($) {

    $.fn.find2 = function (selector) {
        // A find() that also return matches on the root element(s)
        return this.filter(selector).add(this.find(selector));
    };

    kotti.dirtyForms = function (node) {
        var forms = $("form").not("[class~=dirty-ignore]"),
            initial = forms.serialize();

        $(window).unbind('beforeunload');
        forms.submit(function () { $(window).unbind('beforeunload'); });
        if (tinyMCE !== undefined) {
            tinyMCE.triggerSave(true);
        }
        $(window).bind("beforeunload", function () {
            if (tinyMCE !== undefined) {
                tinyMCE.triggerSave(true);
            }
            if ($("form").serialize() !== initial) {
                return "Your changes have not been saved.\nAre you sure you want to leave this page?";
            }
            return null;
        });
    };

    kotti.domChanged = function (node) {
        $.each(kotti.domChangedHandlers, function (index, func) {
            func(node);
        });
    };

    kotti.main = function (handlers) {
        var node = $('html');
        if (!handlers) {
            handlers = [
            ];
        }
        $.each(handlers, function (index, func) {
            kotti.domChangedHandlers.push(func);
        });
        kotti.domChanged(node);
    };

    // deform might be undefined, e.g. in kotti_tinymce's kottibrowser
    if (window.deform) {
        deform.load();
    }

    kotti.main();

}(jQuery));
