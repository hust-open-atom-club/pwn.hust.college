function loadScoreboard(duration, page) {
    const dojo = init.dojo;
    const module = init.module || "_";
    const scoreboard = $("#scoreboard");

    const endpoint = `/pwncollege_api/v1/scoreboard/${dojo}/${module}/${duration}/${page}`;
    scoreboard.empty();
    let message = "Loading."
    scoreboard.html(`<td colspan=6>${message}</td>`);
    setTimeout(function loadmsg() {
        if (scoreboard.html().includes(message)) {
            message += "."
            scoreboard.html(`<td colspan=6>${message}</td>`);
            setTimeout(loadmsg, 1000);
        }
    }, 500);
    $("#scoreboard-control-week").removeClass("scoreboard-page-selected");
    $("#scoreboard-control-month").removeClass("scoreboard-page-selected");
    $("#scoreboard-control-all").removeClass("scoreboard-page-selected");
    if (duration == 7) $("#scoreboard-control-week").addClass("scoreboard-page-selected");
    if (duration == 30) $("#scoreboard-control-month").addClass("scoreboard-page-selected");
    if (duration == 0) $("#scoreboard-control-all").addClass("scoreboard-page-selected");

    CTFd.fetch(endpoint, {
        method: "GET",
        credentials: "same-origin",
        headers: {
            Accept: "application/json",
            "Content-Type": "application/json"
        },
    }).then(response => {
        return response.json()
    }).then(result => {
        scoreboard.empty();

        const standings = result.standings;
        if (result.me) {
            if (result.me.rank < standings[0].rank)
                standings.splice(0, 0, result.me)
            else if (result.me.rank > standings[standings.length - 1].rank)
                standings.splice(standings.length, 0, result.me)
        }
        standings.forEach(user => {
            const row = $(`
            <tr>
              <td scope="row" class="col-md-1"><b></b></td>
              <td class="col-md-1 p-0">
                <img class="scoreboard-symbol">
              </td>
              <td class="col-md-4">
                <a class="scoreboard-name text-decoration-none">
                </a>
              </td>
              <td class="scoreboard-completions col-md-4">
              </td>
              <td class="col-md-1">
                <img class="scoreboard-belt">
              </td>
              <td class="col-md-1"><b></b></td>
            </tr>
            `);
            row.find("td").eq(0).find("b").text(`#${user.rank}`);
            row.find(".scoreboard-symbol").attr("src", user.symbol);
            row.find(".scoreboard-name").attr("href", user.url);
            row.find(".scoreboard-belt").attr("src", user.belt);
            row.find("td").eq(5).find("b").text(user.solves);
            row.find(".scoreboard-name").text(user.name.slice(0, 50));

            user.badges.forEach(badge => {
                const badgeSpan = $(`
                    <span>
                    <a>
                    <img class="scoreboard-emoji"></img>
                    </a>
                    </span><span> </span>
                `);
                badgeSpan.first().attr("title", badge.text);
                badgeSpan.find("a").attr("href", badge.url || "#");
                badgeSpan.find("img").attr("src", `/themes/dojo_theme/static/img/dojo/${badge.emoji}.svg`);
                if (badge.count > 1)
                    badgeSpan.find("a").after($("<sub>").text(`x${badge.count}`));
                row.find(".scoreboard-completions").append(badgeSpan);
            })

            if (result.me && user.user_id == result.me.user_id)
                row.addClass("scoreboard-row-me");
            scoreboard.append(row);
        });

        const scoreboardPages = $("#scoreboard-pages");
        scoreboardPages.empty();//A
        if (result.pages.length > 1) {
            result.pages.forEach(i => {
                const pageButton = $(`
                <li class="scoreboard-page"><a href="javascript:loadScoreboard('${duration}', ${i})">${i}</a></li>
                `);
                pageButton.addClass(i == page ? "scoreboard-page-selected" : "scoreboard-page-unselected");
                scoreboardPages.append(pageButton);
            });
        }
    });
}