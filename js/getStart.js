$(document).ready(function(){
    // This following code is got form 
    // http://stackoverflow.com/questions/8130069/load-bootstrap-js-popover-content-with-ajax
    $("body").delegate('.withAjaxPopover','hover',function(event){
        if (event.type === 'mouseenter') {
            var el=$(this);
            $.post(el.attr('data-load'),function(d){
                var content = {content: "You've learnt "+d.count+" words!"};
                el.unbind('hover').popover(content).popover('show');
            });
        }  else {
            $(this).popover('hide');
        }
    });
});
