# Project 1 (125 pts)

## Part 1: http client (30%, 37.5 pts)
- Basic functionalities (25 pts in total)
  - (10) Program does not crash or "technically run forever"
  - (8) Able to show html webpage quickly (no redirect, canonical)
    - (-1) if page correct, but took too long time to respond
    - (-4) if showed the page partially (similarity score > some threshold)
    - (-8) if failed
  - (1) exit 0
  - (1) empty stderr
  - (5) **Special** robustness: for each potential functionalities to add, program does not crash or "technically run forever"
    - (-1) for each crash / time out, until 0
- Additional functionalities (12.5 pts in total)
  - (1.5) 301/302-redirected, when succeed, show the page (1), exit 0 (0.5)
  - (1.5) 301/302-redirected, when failed to https, should print the redirected chain in stderr (1), exit !0 (0.5)
  - (1.5) 301/302-redirected, when chain too long, should print the website 9-11 times in stderr (1), exit !0 (0.5)
  - (1) upon 404, still print the body (0.5), exit !0 (0.5)
  - (1) upon non-text/html, print nothing (0.5), and exit !0 (0.5)
  - (1.5) should show the desired page when port number is given (don't check exit code)
  - (1.5) should show the page without "/" (don't check exit code)
  - (1.5) should be able to show large pages (don't check exit code)
  - (1.5) should show the page when content-length header is missing (don't check exit code)

## Part 2: http server for a single connection (30%, 37.5 pts)
- Basic (25) open the server, visit `rfc2616.html` page
  - (5) `curl` should not crash / timed out
    - if `curl` returned non-zero code, if may because header is not correct, so duplicate with next test
  - (5) Header Should be correct:
    - (-5) if status code is not 200
    - ~~(-2) if content-type missing or not corrent~~
  - (10) Should show page when we `curl`, before it exits or before we kill it:
    - (-5) if it got an incomplete page (similarity score > some threshold)
    - (-10) if it returned a wrong page, or no page at all
  - (5) Should stay running (until we kill)
    - (-5) if server crashed
    - (-5) if server crashed after refreshing
    - (-5) if server crashed / exited with code 0
- Additional (12.5)
  - (5) Return 403 forbidden
    - (-5) if no return, `curl` time out, wrong status code
    - (-2) if everything alright but server exited or crashed, or curl timeout
  - (5) Return 404 not found
    - (-5) if no return, `curl` time out, wrong status code
    - (-2) if everything alright but server exited or crashed, or curl timeout
  - (2.5) refreshability: visiting the rfc page after 403/404 test
    - (-2.5) did not show the page every time

## Part 3: http server for multi connection (30%, 37.5 pts)
- Basic (25)
  - (5) `curl` should not crash / timeout
  - (10) Should show page when we `curl`, before it exits or before we kill it:
    - (-5) if it got a correct page, but time > 2.5s and time < 10s
    - (-5) if it got an inaccurate page (similarity score > some threshold)
    - (-10) if it returned a wrong page, or no page at all
  
  - (10) Should stay running (until we kill)
    - (-10) if server exited with code 0
    - (-10) if server crashed after visit
    - (-7) if server crashed after we closed telnet  
- Additional (12.5)
  - (7.5) stablility: visiting the rfc page for 5 times in a row
    - (-2.5) if at least one connection too slow, > 2.5s, but all succeed
    - (-5) two connections are too slow, > 2.5s
    - (-7.5) three connection are too slow, > 2.5s
    - (-1.5) if one page are incomplete, at most remove 4.5
  - (5) scalability: 3 telnet connections
    - (-2.5) too slow
    - (-5) telnet failed
    - (-5) curl failed
    - (-5) no content return

## Part 4: dynamic web server (10%, 12.5 pts)
- Basic (6.5), 4 * 5 * 6 = 120
  - (2) `curl` returns right json body
  - (2) right header "Content-Type: application/json"
  - (0.5) `curl` should not crash / timed out
  - (2) server should stay running
    
- Additional (6) only care about curl's output
  - (1) only check status code, 404 not found
  - (1) only check status code, 400 when no number
  - (1) only check status code, 400 when non-number
  - (1) only check json body, when "inf" * 3 = "inf"
  - (1) only check json body, when 10 ** 200 ** 3
  - (1) only check json body, when one parameter: -5 = -5
## using banned librarys (TODO)
Give a zero score for that part if the followings are detected: `TODO`

## Late policy (leave for discussion)
- 1 days == 10% off
- 2 days == 20% off
- 3+ days == report to Prof. Tarzia

Night threshold: TBD (I tried, but finally decided that it should be flexible and kept unknown to students)
