(function($) {

    function dirty_forms() {
        function forms() { return $("form").not("[class~=dirty-ignore]"); }

        forms().submit(function() { $(window).unbind('beforeunload'); });
        var initial = forms().serialize();
        $(window).bind("beforeunload", function() {
            if (tinyMCE != undefined)
                tinyMCE.triggerSave(true);
            if ($("form").serialize() != initial) {
                return "Your changes have not been saved.\nAre you sure you want to leave this page?";
            }
            return null;
        });
    }

    function dropdowns() {
        $(".dropdown-trigger").click(function () {
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

    function collapse() {
        $(".collapse").each(function() {
            $(this).find("ul").hide();
            function show() {
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

    function hover_link_enable() {
        $(".hover-link").removeClass("hover-link");

        $(".hover-link-enable").hover(
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

    $(document).ready(function() {
        deform.load();
        dirty_forms();
        dropdowns();
        collapse();
        hover_link_enable();
    });


 })(jQuery);
