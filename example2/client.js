/*eslint-env jquery*/
/* global io */

const PORT = 5050

$(document).ready(() => {
  // sending a connect request to the server.
  const projectId = $("#projectId").val()
  const runElem = $("#runctl")
  const killElem = $("#killctl")
  const runFeedbackElem = $("#runfeedback")
  const runActorElem = $("#runactor")
  const killActorElem = $("#killactor")
  const progressElem = $("#progress")
  const statusElem = $("#status")

  const setRunActor = you => {
    runActorElem.attr("actor", you ? "you" : "")
  }
  const putRunActor = () => {
    if (runActorElem.attr("actor") == "you") {
      runActorElem.html("triggered by you ...").attr("class", "good")
    } else {
      runActorElem.html("triggered by somebody else ...").attr("class", "warning")
    }
  }
  const setKillActor = you => {
    killActorElem.attr("actor", you ? "you" : "")
  }
  const clearKillActor = () => {
    killActorElem.attr("actor", "")
    killActorElem.html("")
  }
  const putKillActor = () => {
    if (killActorElem.attr("actor") == "you") {
      killActorElem.html("killed by you ...").attr("class", "good")
    } else {
      killActorElem.html("killed by somebody else ...").attr("class", "warning")
    }
  }

  const startOuterNo = () => {
    runFeedbackElem
      .html("task suppressed because it is already running")
      .attr("class", "warning")
  }
  const startOuter = () => {
    runFeedbackElem.html("task accepted")
    setRunActor(true)
  }
  const startInner = () => {
    runFeedbackElem.html("")
    putRunActor()
    setKillActor(false)
    clearKillActor()
    progressElem.html("")
    statusElem.html("in progress ...").attr("class", "warning")
  }
  const successInner = () => {
    statusElem.html("OK").attr("class", "good")
    runFeedbackElem.html("task completed")
    setRunActor(false)
  }
  const failureInner = msg => {
    statusElem.html(`Error (${msg})`).attr("class", "error")
    runFeedbackElem.html("task failed")
    setRunActor(false)
  }
  const killOuterNo = () => {
    killActorElem
      .html("task is not running, nothing to kill")
      .attr("class", "warning")
  }
  const killOuter = () => {
    setKillActor(true)
  }
  const killInner = () => {
    putKillActor()
    statusElem.html("Error (killed)").attr("class", "error")
    setRunActor(false)
  }
  const unKnownStatus = msg => {
    runFeedbackElem.html(`?? ${msg}`)
  }

  const setStatus = (pid, stat, msg) => {
    if (stat == "start-outer-no") {
      startOuterNo()
    } else if (stat == "start-outer") {
      startOuter()
    } else if (stat == "start-inner") {
      startInner()
    } else if (stat == "success-inner") {
      successInner()
    } else if (stat == "failure-inner") {
      failureInner(msg)
    } else if (stat == "kill-outer-no") {
      killOuterNo()
    } else if (stat == "kill-outer") {
      killOuter()
    } else if (stat == "kill-inner") {
      killInner()
    } else {
      unKnownStatus(msg)
    }
  }

  const runOK = response => {
    const { pid, stat } = response
    setStatus(pid, stat)
  }

  const runError = (jqXHR, stat) => {
    const { status, statusText } = jqXHR
    $("#status").html(`Error ${stat} ${status} ${statusText}`).addClass("error")
  }

  const killOK = response => {
    const { pid, stat } = response
    setStatus(pid, stat)
  }

  const killError = (jqXHR, stat) => {
    const { status, statusText } = jqXHR
    $("#status").html(`Error ${stat} ${status} ${statusText}`).addClass("error")
  }

  const setupButtons = () => {
    runElem.off("click").click(() => {
      $.ajax({
        type: "POST",
        headers: { "Content-Type": "application/json" },
        url: `/project/${projectId}/run`,
        data: JSON.stringify({}),
        processData: false,
        contentType: true,
        success: runOK,
        error: runError,
      })
    })
    killElem.off("click").click(() => {
      $.ajax({
        type: "POST",
        headers: { "Content-Type": "application/json" },
        url: `/project/${projectId}/kill`,
        data: JSON.stringify({}),
        processData: false,
        contentType: true,
        success: killOK,
        error: killError,
      })
    })
  }

  const socket = io.connect(`http://localhost:${PORT}`)

  socket.on("after connect", msg => {
    console.log("After connect", msg)
  })

  socket.on("progress", msg => {
    const { pid, step } = msg
    if (pid == projectId) {
      console.log(`progress ${step}...`)
      progressElem.append(`Step ${step}<br>`)
    }
  })

  socket.on("status", msg => {
    const { pid, stat } = msg
    if (pid == projectId) {
      console.log(`status ${stat}...`)
      setStatus(pid, stat)
    }
  })

  setupButtons()
})
