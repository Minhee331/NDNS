function search(){
    let searchVal = document.getElementById("searchVal").value;
    location.href = "/search/"+searchVal;
}

document.getElementById("search").setAttribute('onclick','search();')