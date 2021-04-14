
document.getElementById("searchVal").setAttribute('onkeyup','if(window.event.keyCode==13){search();}');
document.getElementById("search").setAttribute('onclick','search();');

function search(){
    let searchVal = document.getElementById("searchVal").value;
    location.href = "/search/"+searchVal;
}