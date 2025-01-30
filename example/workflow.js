/*eslint-env jquery*/
/* global io */

const PORT = 5050
const tasks = ["function", "script"]

$(document).ready(() => {
  let now = Date.now()
  const elapsed = () => {
    const interval = (Date.now() - now) / 1000
    return interval < 10 ? ` ${interval.toFixed(2)}s` : `${interval.toFixed(0)}s   `
  }
  const progressElem = {}
  const statusElem = {}
  for (const task of tasks) {
    progressElem[task] = $(`#progress${task}`)
    statusElem[task] = $(`#status${task}`)
  }

  const setStatus = arg => {
    const { tm, ctm, task, stat, msg } = arg
    const tmRep = `server ${tm} client ${ctm}`
    const pElem = progressElem[task]
    const sElem = statusElem[task]
    if (stat == "start-issued") {
      sElem.html(`«${task}» command issued`).attr("class", "")
    } else if (stat == "start-prevented") {
      sElem.html(`«${task}» command already running`).attr("class", "")
    } else if (stat == "start") {
      pElem.html("")
      sElem.html(`«${task}» command started`).attr("class", "")
    } else if (stat == "kill-issued") {
      sElem.html(`«${task}» kill signalled`).attr("class", "warning")
    } else if (stat == "kill") {
      sElem.html(`«${task}» killed`).attr("class", "warning")
    } else if (stat == "kill-prevented") {
      sElem.html(`«${task}» command was not running`).attr("class", "")
    } else if (stat == "success") {
      sElem.html(`${tmRep}: «${task}» status OK`).attr("class", "good")
    } else if (stat == "failure") {
      sElem.html(`${tmRep}: «${task}» status Error (${msg})`).attr("class", "error")
    } else if (stat == "interrupt") {
      sElem
        .html(`${tmRep}: «${task}» status Interrupt (${msg})`)
        .attr("class", "warning")
    }
  }

  const responseOK = task => response => {
    const { stat, msg } = response
    setStatus({ stat, task, msg })
  }

  const responseError = task => (jqXHR, stat) => {
    const { status, statusText } = jqXHR
    const statusElem = $(`#status${task}`)
    statusElem.html(`Error ${stat} ${status} ${statusText}`).attr("class", "error")
  }

  const respondClick = task => aUrl => {
    now = Date.now()
    $.ajax({
      type: "POST",
      headers: { "Content-Type": "application/json" },
      url: aUrl,
      data: JSON.stringify({}),
      processData: false,
      contentType: true,
      success: responseOK(task),
      error: responseError(task),
    })
  }
  const setupButtons = () => {
    for (const task of tasks) {
      const runButtonId = `#run${task}`
      const killButtonId = `#kill${task}`
      const runUrl = `/run/${task}/`
      const killUrl = `/kill/${task}/`
      $(runButtonId)
        .off("click")
        .click(() => {
          respondClick(task)(runUrl)
        })
      $(killButtonId)
        .off("click")
        .click(() => {
          respondClick(task)(killUrl)
        })
    }
  }

  const socket = io.connect(`http://localhost:${PORT}`)

  socket.on("after connect", msg => {
    console.log("After connect", msg)
  })

  socket.on("progress", msg => {
    const ctm = elapsed()
    const { tm, task, kind, text } = msg
    const msgRep = `server ${tm}, client ${ctm}: «${task}» [${kind.slice(
      0,
      3
    )}] ${text}`
    ;(kind == "error" ? console.warn : console.log)(msgRep)
    progressElem[task].append(`<div class="msg ${kind}">${msgRep}</div>`)
  })

  socket.on("status", message => {
    const ctm = elapsed()
    const { tm, task, stat, msg } = message
    const msgRep = msg ? `(${msg})` : ""
    const statRep = `server ${tm}, client ${ctm}: «${task}» status ${stat} (${msgRep})`
    console.log(statRep)
    setStatus({ tm, ctm, task, stat, msg })
  })

  setupButtons()
})
