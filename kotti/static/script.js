(function($) {

    function dirty_forms() {
        function forms() { return $("form").not("[class~=dirty-ignore]"); }

        forms().submit(function() { $(window).unbind('beforeunload'); });
        var initial = forms().serialize();
        $(window).bind("beforeunload", function() {
            if (tinyMCE)
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
            target.css("left", $(this).position().left);

            if (!target.hasClass("open")) {
                $("body").click(function() {
                    target.removeClass("open");
                    $(this).unbind("click");
                });
            }
            target.toggleClass("open");
            return false;
        });
    }

    function collapse() {
        $("form.collapse").each(function() {
            $(this).children("ul").hide();
            $(this).click(function() {
                $(this).children("ul").show("fast");
                $(this).unbind("click");
            });
        });
    }

    $(document).ready(function() {
        deform.load();
        dirty_forms();
        dropdowns();
        collapse();
    });


 })(jQuery);
