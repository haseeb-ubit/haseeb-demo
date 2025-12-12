$(document).ready(function () {
    // Sticky header functionality
    var $headBar = $('#header');
    var sticky = $headBar.offset().top;

    $(window).on('scroll', function () {
        if ($(window).scrollTop() >= sticky + 1) {
            $headBar.addClass('active');
        } else {
            $headBar.removeClass('active');
        }
    });


    $('#about_us_menu').addClass('resize');
    //alert("Class 'resize' added to #menu_about_us.");














	//$(".showDD").click(function(navfun){
	//	navfun.stopPropagation();
	//	$(".ddBox").slideUp(0);
	//	if($(this).hasClass("active")){
	//			$(".showDD").removeClass("active");
	//			$(this).next(".ddBox").slideUp(0);
	//	}
	//	else{
	//			$(".showDD").removeClass("active");
	//			$(this).addClass("active");
	//			$(this).next(".ddBox").slideDown(300);
	//	}
	//});

	//	$(".ddBox").click(function (navfun) {
	//		navfun.stopPropagation();
	//	});
	//	$("body").click(function () {
	//		$('.ddBox').slideUp(0);
	//		$('.showDD').removeClass('active');
	//	});


	//	$(".showMobMenu").click(function (navmain) {
	//		navmain.stopPropagation();
	//		$(this).toggleClass('active');
	//		$(this).next('.menu').toggleClass('active');
	//		$('.menuBox').toggleClass('active');


	//	});
	//	$(".menu").click(function (navmain) {
	//		navmain.stopPropagation();
	//	});
	//	$("body").click(function () {
	//		$('.showMobMenu').removeClass('active');
	//		$('.menu').removeClass('active');
	//		$('.menuBox').removeClass('active');
	//	});

	//	$(".showSearch").click(function () {
	//		$("#search").toggleClass('active');
	//		$('.showMobMenu').removeClass('active');
	//		$('.menu').removeClass('active');
	//		$('.menuBox').removeClass('active');
	//	});


		$(".showVideo").click(function(){
			var videoid = $(this).attr('data-');
			$("#videoPopup").show(300);
			$("body").css('overflow', 'hidden');
			$("#video").attr('src', videoid)

		});
		$(".closeVideo").click(function(){
			$("#video").attr('src', '')
			$("body").css('overflow', 'auto');
			$("#videoPopup").hide(0);
		});

		$('a.scroll[href^="#"]').on('click.smoothscroll',function(event) {
			event.preventDefault();
			var target = this.hash,
			$target = jQuery(target);
			$('html, body').stop().animate( {
				'scrollTop': $target.offset().top-155
			}, 900, 'swing');
		});

		$(".faqList li .q").click(function () {
			$(this).next('.ans').slideToggle();
			$(this).parents('li').toggleClass('active');
		});

		var sectionIds = $('a.scroll2');

		sectionIds.click(function(event) {
			event.preventDefault();

			var target = $(this).attr('href');
			var targetOffset = $(target).offset().top - 90;

			$('html, body').animate({
				scrollTop: targetOffset
			}, 600);
		});

		$(document).scroll(function() {
			sectionIds.each(function() {
				var container = $(this).attr('href');
				var containerOffset = $(container).offset().top - 90;
				var containerHeight = $(container).outerHeight();
				var containerBottom = containerOffset + containerHeight;
				var scrollPosition = $(document).scrollTop();

				if (scrollPosition < containerBottom - 20 && scrollPosition >= containerOffset - 20) {
					$(this).addClass('active');
				} else {
					$(this).removeClass('active');
				}
			});
		});

});

