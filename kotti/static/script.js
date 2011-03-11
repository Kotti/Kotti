(function($) {

    $.fn.find2 = function(selector) {
        // A find() that also return matches on the root element(s)
        return this.filter(selector).add(this.find(selector));
    };

    function replace_html(html) {
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
            dom_changed(new_el);
        });
    }

    function ajax_forms(els) {
        els.find2("form.ajax").ajaxForm({
            success: replace_html
        });
    }

    function dirty_forms(els) {
        var forms = $("form").not("[class~=dirty-ignore]");
        $(window).unbind('beforeunload');
        forms.submit(function() { $(window).unbind('beforeunload'); });
        var initial = forms.serialize();
        $(window).bind("beforeunload", function() {
            if (tinyMCE != undefined)
                tinyMCE.triggerSave(true);
            if ($("form").serialize() != initial) {
                return "Your changes have not been saved.\nAre you sure you want to leave this page?";
            }
            return null;
        });
    }

    function dropdowns(els) {
        els.find2(".dropdown-trigger").click(function () {
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
    }

    function collapse(els) {
        els.find2(".collapse").each(function() {
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
    }

    function hover_link_enable(els) {
        els.find2(".hover-link").removeClass("hover-link");

        els.find2(".hover-link-enable").hover(
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
    }

    function dom_changed(els) {
        ajax_forms(els);
        dirty_forms(els);
        dropdowns(els);
        collapse(els);
        hover_link_enable(els);
    }

    $(document).ready(function() {
        var els = $('html');
        deform.load();
        dom_changed(els);
    });


 })(jQuery);
