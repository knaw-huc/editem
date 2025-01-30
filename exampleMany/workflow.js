/*eslint-env jquery*/
/* global io */

const PORT = 5050
let now = Date.now()

$(document).ready(() => {
  // sending a connect request to the server.
  const elapsed = () => {
    const interval = (Date.now() - now) / 1000
    return interval < 10 ? `${interval.toFixed(2)}s` : `${interval.toFixed(0)}s`
  }
  const progressElem = $("#progress")
  const statusElem = $("#status")

  const setStatus = (tm, ctm, stat, msg) => {
    const tmRep = `server ${tm} client ${ctm}`
    if (stat == "start-inner") {
      progressElem.html("")
      statusElem.html("")
    } else if (stat == "success-inner") {
      statusElem.html(`${tmRep}: status OK`)
    } else if (stat == "failure-inner") {
      statusElem.html(`${tmRep}: status Error (${msg})`)
    }
  }

  const runOK = response => {
    const { stat } = response
    setStatus(stat)
  }

  const runError = (jqXHR, stat) => {
    const { status, statusText } = jqXHR
    $("#status").html(`Error ${stat} ${status} ${statusText}`).addClass("error")
  }

  const runClick = runUrl => {
    now = Date.now()
    $.ajax({
      type: "POST",
      headers: { "Content-Type": "application/json" },
      url: runUrl,
      data: JSON.stringify({}),
      processData: false,
      contentType: true,
      success: runOK,
      error: runError,
    })
  }
  const setupButtons = () => {
    for (const thr of ["t", "d"]) {
      for (const que of ["q", "d"]) {
        for (const what of ["function", "script", "scriptnb"]) {
          const buttonId = `#run${what}${thr}${que}`
          const runUrl = `/run/${what}/${thr}/${que}/`
          $(buttonId)
            .off("click")
            .click(() => {
              runClick(runUrl)
            })
        }
      }
    }
  }

  const socket = io.connect(`http://localhost:${PORT}`)

  socket.on("after connect", msg => {
    console.log("After connect", msg)
  })

  socket.on("progress", msg => {
    const ctm = elapsed()
    const { tm, kind, text } = msg
    const msgRep = `server ${tm}, client ${ctm}: [${kind}] ${text}`
    console.log(msgRep)
    progressElem.append(`${msgRep}<br>`)
  })

  socket.on("status", message => {
    const ctm = elapsed()
    const { tm, stat, msg } = message
    const msgRep = msg ? `(${msg})` : ""
    const statRep = `server ${tm}, client ${ctm}: status ${stat} (${msgRep})`
    console.log(statRep)
    setStatus(tm, ctm, stat, msg)
  })

  setupButtons()
})
