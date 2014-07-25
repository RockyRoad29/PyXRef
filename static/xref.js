$('#hover-demo2 p').hover(function() {
  $(this).addClass('pretty-hover');
}, function() {
  $(this).removeClass('pretty-hover');
});

$('table.hover-grid td').mouseover(function () {
    $(this).siblings().css('background-color', '#EAD575');
    var ind = $(this).index();
    $('td:nth-child(' + (ind + 1) + ')').css('background-color', '#EAD575');
});
$('table.hover-grid td').mouseleave(function () {
    $(this).siblings().css('background-color', '');
    var ind = $(this).index();
    $('td:nth-child(' + (ind + 1) + ')').css('background-color', '');
});
