/**
 * document.addEventListener("DOMContentLoaded", function() {
    const resizeButton = document.getElementById("resize-menu");
    const menu_class = document.getElementById("left-menu").classList;
    const cookieName = "resized-menu";
    const normalSizeClass = "col-lg-2";
    const resizeButtonIconClasses = resizeButton.querySelector("i").classList;
    const getResizeCookie = function() {
        try {
            return document.cookie
              .split('; ')
              .find(row => row.startsWith(cookieName + '='))
              .split('=')[1];
        } catch (e) {
            return "false";
        }
    };
    const setResizeCookie = function(value) {
        document.cookie = cookieName+"="+value.toString();
    };
    const changeExpandIcon = function(is_reduced) {
        if (is_reduced === "true"){
            resizeButtonIconClasses.replace("fa-compress", "fa-expand");
        } else {
            resizeButtonIconClasses.replace("fa-expand", "fa-compress");
        }
    }
    const resizeLeftMenu = function(localStorageEvent=true) {
        menu_class.toggle(normalSizeClass);
        menu_class.toggle("folded-left-col");
        let is_reduced = !menu_class.contains("col-lg-2");
        changeExpandIcon(is_reduced.toString());
        if(!localStorageEvent){
           setResizeCookie(is_reduced);
        }
    };
    document.getElementById("left-menu").addEventListener('animationend', () => {
      if(!menu_class.contains("animated")) {
          menu_class.add("animated");
      }
    });
    resizeButton.addEventListener("click", function(e) {
        e.preventDefault();
        resizeLeftMenu(false);
    });

    if(!menu_class.contains("animated") && menu_class.contains(normalSizeClass)) {
          menu_class.add("animated");
    }
    changeExpandIcon(getResizeCookie());

});
*/