$(document).ready(function(){
    var options = {title: "click on the word to remind it later"};
    $(".wordName").tooltip(options);
    $(".wordElement").click(function(){
        var element = $(this);
        var wordName = element.children().children(".wordName").text();
        var style = element.css("text-decoration");
        var lineThrough = "line-through";
        if(style != lineThrough){
            element.css("text-decoration", lineThrough);
            $.post("/remove/word", {term: wordName}, function(data){
                ;
            });
        }else{
            element.css("text-decoration", "");
            $.post("/add/word", {term: wordName}, function(data){
                ;
            });
        }
    });
});
