(function($) {

    function dirty_forms() {
        function forms() { return $("form").not("[class~=dirty-ignore]"); }
        
        forms().submit(function() { $(window).unbind('beforeunload'); });
        var initial = forms().serialize();
        $(window).bind('beforeunload', function() {
            if (tinyMCE)
                tinyMCE.triggerSave(true);
            if ($("form").serialize() != initial) {
                return "Your changes have not been saved.\nAre you sure you want to leave this page?"
            }
        });
    }

    $(document).ready(function() {
        deform.load();
        dirty_forms();
    });


 })(jQuery);
