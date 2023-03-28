function projectMemberDelete(id, pid){
    if (confirm("Are you sure?") == true) {
     window.location.href = "/projectMemberRemove/"+pid+"/"+id;
    }   
  }
  function memberPromote(id){
    if (confirm("Are you sure?") == true) {
     window.location.href = "/memberPromote/"+"{{team.id}}/"+id;
    }   
  }
  function memberDelete(id){
      if (confirm("Are you sure?") == true) {
       window.location.href = "/memberRemove/"+"{{team.id}}/"+id;
      }   
    }
    function projectMemberDelete(id){
      if (confirm("Are you sure?") == true) {
       window.location.href = "/projectMemberRemove/"+"{{project.id}}/"+id;
      }   
    }
    function memberPromote(id){
      if (confirm("Are you sure?") == true) {
       window.location.href = "/memberPromote/"+"{{team.id}}/"+id;
      }   
    }