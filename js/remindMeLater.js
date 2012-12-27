$(document).ready(function(){
    var options = {title: "click on the word to remind it later"};
    $(".wordName").tooltip(options);
    $(".wordElement").click(function(){
        var element = $(this)
        var style = element.css("text-decoration");
        var lineThrough = "line-through";
        if(style != lineThrough){
            element.css("text-decoration", lineThrough);
        }else{
            element.css("text-decoration", "");
        }
    });
});
