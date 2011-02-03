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
