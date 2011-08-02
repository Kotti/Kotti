var kotti = {
    dom_changed_handlers: new Array()
};

(function($) {

    $.fn.find2 = function(selector) {
        // A find() that also return matches on the root element(s)
        return this.filter(selector).add(this.find(selector));
    };

    kotti.replace_html = function(html) {
        // This function looks for nodes in the received HTML with the
        // class "ajax-replace" and replaces nodes in the current DOM
        // with matching *ids*.
        var root = $(html);
        var selector = null;
        var new_el = null;
        root.find2(".ajax-replace").each(function() {
            if (this.id == "") {
                throw "Found .ajax-replace elemnt without id: " + this;
            }

            selector = "#" + this.id;
            $(selector).replaceWith(this);
            new_el = $(selector);
            kotti.dom_changed(new_el);
        });
    };

    kotti.ajax_forms = function(node) {
        node.find2("form.ajax").ajaxForm({
            success: kotti.replace_html
        });
    };

    kotti.messages = function(node) {
        node.find2("#messages").hide();
        node.find2(".message").each(function() {
            var type = "notice";
            var msg = $(this);
            var text = msg.html();
            var stayTime = 3000;

            if (msg.hasClass("success"))
                type = "success";
            else if (msg.hasClass("error")) {
                type = "error";
                stayTime = 6000;
            }

            $().toastmessage('showToast', {
                text: text,
                type: type,
                stayTime: stayTime
            });

        });
    };

    kotti.dirty_forms = function(node) {
        var forms = $("form").not("[class~=dirty-ignore]");
        $(window).unbind('beforeunload');
        forms.submit(function() { $(window).unbind('beforeunload'); });
        if (tinyMCE != undefined)
            tinyMCE.triggerSave(true);
        var initial = forms.serialize();
        $(window).bind("beforeunload", function() {
            if (tinyMCE != undefined)
                tinyMCE.triggerSave(true);
            if ($("form").serialize() != initial) {
                return "Your changes have not been saved.\nAre you sure you want to leave this page?";
            }
            return null;
        });
    };

    kotti.dropdowns = function(node) {
        node.find2(".dropdown-trigger").click(function () {
            var target = $($(this).attr("href"));
            // move the dropdown to the correct position
            target.css("left", $(this).position().left);
            $("body").click(function() {
                target.hide();
                $(this).unbind("click");
            });
            target.toggle();
            return false;
        });
    };

    kotti.collapse = function(node) {
        node.find2(".collapse").each(function() {
            $(this).find("ul").hide();
            $(this).addClass("collapsed");
            function show() {
                $(this).removeClass("collapsed");
                var child = $(this).find("ul:hidden");
                if (child.length != 0) {
                    $(this).find("ul").show(400);
                    $("body").animate(
                        {scrollTop: $(this).offset().top - 15}, 400);
                    $(this).unbind("click");
                    $(this).unbind("hover");
                }
            };
            $(this).click(show);
            $(this).hover(show);
        });
    };

    kotti.hover_link_enable = function(node) {
        node.find2(".hover-link").removeClass("hover-link");

        node.find2(".hover-link-enable").hover(
            function() { $(this).addClass("hover-link"); },
            function() { $(this).removeClass("hover-link"); }
        ).click(function() {
            var link = $("a", $(this));
            var target = link.attr("target");
            if (!target)
                target = "_self";
            window.open(link.attr("href"), target);
            return false;
        });
    };

    kotti.dom_changed = function(node) {
        $.each(kotti.dom_changed_handlers, function(index, func) {
            func(node);
        });
    };

    kotti.main = function(handlers) {
        var node = $('html');
        if (!handlers) {
            handlers = [
                kotti.messages, kotti.ajax_forms, kotti.dirty_forms,
                kotti.dropdowns, kotti.collapse, kotti.hover_link_enable
            ];
        }
        $.each(handlers, function(index, func) {
            kotti.dom_changed_handlers.push(func);
        });
        kotti.dom_changed(node);
    };

 })(jQuery);
