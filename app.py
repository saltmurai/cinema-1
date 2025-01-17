import mysql.connector
import sys
import datetime
from mysql.connector import Error
from flask import Flask, request, jsonify, render_template, session
from random import randint
from flask_mysqldb import MySQL as flask_mysql
import MySQLdb.cursors

app = Flask(__name__)
app.secret_key = "1234nf"

# Database connection detail
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "sang"
app.config["MYSQL_PASSWORD"] = "sang"
app.config["MYSQL_DB"] = "db_theatre"

# Init MySQL
flask_sql = flask_mysql(app)


# login
@app.route("/")
def renderLoginPage():
    return render_template("login.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    # Output message if something goes wrong...
    # Check if "username" and "password" POST requests exist (user submitted form)
    msg = ""
    if (
        request.method == "POST"
        and "username" in request.form
        and "password" in request.form
    ):
        # Create variables for easy access
        username = request.form["username"]
        password = request.form["password"]
        # Check if account exists using MySQL
        cursor = flask_sql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            "SELECT * FROM accounts WHERE username = %s AND password = %s",
            (
                username,
                password,
            ),
        )
        # Fetch one record and return result
        account = cursor.fetchone()
        # If account exists in accounts table in out database
        if account:
            # Create session data, we can access this data in other routes
            session["loggedIn"] = True
            session["id"] = account["id"]
            session["username"] = account["username"]
            session["name"] = account["name"]
            session["role"] = account["role"]
            # cursor.execute("call delete_old()")
            if account["role"] == "cashier":
                cursor.execute("call delete_old()")
                return render_template("cashier.html")
            if account["role"] == "manager":
                cursor.execute("call delete_old()")
                return render_template("manager.html")

            # Account doesnt exist or username/password incorrect
    return render_template("loginfail.html")


# @app.route("/login", methods=["GET", "POST"])
# def verifyAndRenderRespective():
#     username = request.form["username"]
#     password = request.form["password"]

#     try:

#         if username == "manager" and password == "manager":

#             res = runQuery("call delete_old()")
#             return render_template("manager.html")
#         elif username == "cashier" and password == "cashier":
#             res = runQuery("call delete_old()")
#             return render_template("cashier.html")
#         else:
#             res = runQuery(
#                 "SELECT ma_nhan_vien,ten_nhan_vien,so_dien_thoai,chuc_vu FROM nhan_vien WHERE ten_nhan_vien = '"
#                 + username
#                 + "' and so_dien_thoai = '"
#                 + password
#                 + "'"
#             )

#             staffs = []
#             for i in res:
#                 staffs.append([i[0], i[1], i[2], i[3]])
#             if i[0] == "":
#                 return render_template("loginfail.html")
#             else:
#                 if i[3] == "cashier":
#                     res = runQuery("call delete_old()")
#                     return render_template("cashier.html", staffs=staffs)
#                 if i[3] == "manager":
#                     res = runQuery("call delete_old()")
#                     return render_template("manager.html")

#     except Exception as e:
#         print(e)
#         return render_template("loginfail.html")


# Routes for cashier
@app.route("/getMoviesShowingOnDate", methods=["POST"])
def moviesOnDate():
    date = request.form["date"]

    res = runQuery(
        "SELECT DISTINCT movie_id,movie_name,type FROM movies NATURAL JOIN shows WHERE Date = '"
        + date
        + "'"
    )

    if res == []:
        return "<h4>Không có suất chiếu</h4>"
    else:
        return render_template("movies.html", movies=res)


@app.route("/getTimings", methods=["POST"])
def timingsForMovie():
    date = request.form["date"]
    movieID = request.form["movieID"]
    movieType = request.form["type"]

    res = runQuery(
        "SELECT time FROM shows WHERE Date='"
        + date
        + "' and movie_id = "
        + movieID
        + " and type ='"
        + movieType
        + "'"
    )

    list = []

    for i in res:
        list.append((i[0], int(i[0] / 100), i[0] % 100 if i[0] % 100 != 0 else "00"))

    return render_template("timings.html", timings=list)


@app.route("/getShowID", methods=["POST"])
def getShowID():
    date = request.form["date"]
    movieID = request.form["movieID"]
    movieType = request.form["type"]
    time = request.form["time"]

    res = runQuery(
        "SELECT show_id FROM shows WHERE Date='"
        + date
        + "' and movie_id = "
        + movieID
        + " and type ='"
        + movieType
        + "' and time = "
        + time
    )
    return jsonify({"showID": res[0][0]})


@app.route("/getAvailableSeats", methods=["POST"])
def getSeating():
    showID = request.form["showID"]

    res = runQuery(
        "SELECT class,no_of_seats FROM shows NATURAL JOIN halls WHERE show_id = "
        + showID
    )

    totalGold = 0
    totalStandard = 0

    for i in res:
        if i[0] == "gold":
            totalGold = i[1]
        if i[0] == "standard":
            totalStandard = i[1]

    res = runQuery("SELECT seat_no FROM booked_tickets WHERE show_id = " + showID)

    goldSeats = []
    standardSeats = []

    for i in range(1, totalGold + 1):
        goldSeats.append([i, ""])

    for i in range(1, totalStandard + 1):
        standardSeats.append([i, ""])

    for i in res:
        if i[0] > 1000:
            goldSeats[i[0] % 1000 - 1][1] = "disabled"
        else:
            standardSeats[i[0] - 1][1] = "disabled"

    return render_template(
        "seating.html", goldSeats=goldSeats, standardSeats=standardSeats
    )


@app.route("/getPrice", methods=["POST"])
def getPriceForClass():
    showID = request.form["showID"]
    seatClass = request.form["seatClass"]

    res = runQuery("INSERT INTO halls VALUES(-1,'-1',-1)")

    res = runQuery("DELETE FROM halls WHERE hall_id = -1")

    res = runQuery(
        "SELECT price FROM shows NATURAL JOIN price_listing WHERE show_id = " + showID
    )

    if res == []:
        return "<h5>Chưa có giá vé cho suất chiếu này, thử lại sau</h5>"

    price = int(res[0][0])
    if seatClass == "gold":
        price = price + 30

    return (
        "<h5>Ticket Price: "
        + str(price)
        + ',000 VND</h5>\
	<button onclick="confirmBooking()">Xác Nhận</button>'
    )


@app.route("/insertBooking", methods=["POST"])
def createBooking():
    showID = request.form["showID"]
    staffID = session['id']
    seatNo = request.form["seatNo"]
    seatClass = request.form["seatClass"]

    if seatClass == "gold":
        seatNo = int(seatNo) + 1000

    ticketNo = 0
    res = None

    while res != []:
        ticketNo = randint(0, 2147483646)
        res = runQuery(
            "SELECT ticket_no FROM booked_tickets WHERE ticket_no = "
            + str(ticketNo)
        )

    res = runQuery(
        "INSERT INTO booked_tickets VALUES("
        + str(ticketNo)
        + ","
        + str(showID)
        + ","
        + str(seatNo)
        + ","
        + str(staffID)
        + ")"
    )

    if res == []:
        return (
            "<h5>Đặt vé thành công</h5>\
		<h6>Mã vé: "
            + str(ticketNo)
            + "</h6>"
        )


# Routes for manager


# Route for movies
@app.route("/getMovieOption", methods=["POST"])
def getMovieOption():
    return render_template("movieoption.html")


# Add movie route
@app.route("/fetchMovieInsertForm", methods=["GET"])
def getMovieForm():
    return render_template("movieform.html")


@app.route("/insertMovie", methods=["POST"])
def insertMovie():
    movieName = request.form["movieName"]
    movieLen = request.form["movieLen"]
    movieLang = request.form["movieLang"]
    types = request.form["types"]
    startShowing = request.form["startShowing"]
    endShowing = request.form["endShowing"]
    res = runQuery("SELECT * FROM movies")

    for i in res:
        if (
            i[1] == movieName
            and i[2] == int(movieLen)
            and i[3] == movieLang
            and i[4].strftime("%Y/%m/%d") == startShowing
            and i[5].strftime("%Y/%m/%d") == endShowing
        ):
            return "<h5>Phim đã tồn tại</h5>"

    movieID = 0
    res = None

    while res != []:
        movieID = randint(0, 2147483646)
        res = runQuery("SELECT movie_id FROM movies WHERE movie_id = " + str(movieID))

    res = runQuery(
        "INSERT INTO movies VALUES("
        + str(movieID)
        + ",'"
        + movieName
        + "',"
        + movieLen
        + ",'"
        + movieLang
        + "','"
        + startShowing
        + "','"
        + endShowing
        + "')"
    )

    if res == []:
        print("có thể thêm phim")
        subTypes = types.split(" ")

        while len(subTypes) < 3:
            subTypes.append("NUL")

        res = runQuery(
            "INSERT INTO types VALUES("
            + str(movieID)
            + ",'"
            + subTypes[0]
            + "','"
            + subTypes[1]
            + "','"
            + subTypes[2]
            + "')"
        )

        if res == []:
            return (
                "<h5>Phim đã được thêm vào thành công</h5>\
			<h6>Movie ID: "
                + str(movieID)
                + "</h6>"
            )
        else:
            print(res)
    else:
        print(res)

    return "<h5>Đã xảy ra lỗi</h5>"


# Update movie route
@app.route("/getMovieInfo", methods=["GET"])
def movieList():
    res = runQuery("SELECT * FROM movies")

    return render_template("currentmovie.html", movies=res)


@app.route("/setNewMovieInfo", methods=["POST"])
def setMovieInfo():
    movieID = request.form["movieID"]
    newMovieName = request.form["newMovieName"]
    newMovieLen = request.form["newMovieLen"]
    newMovieLanguage = request.form["newMovieLanguage"]
    types = request.form["types"]
    startShowing = request.form["startShowing"]
    endShowing = request.form["endShowing"]
    res = runQuery(
        "UPDATE movies SET movie_name = '"
        + newMovieName
        + "', length = "
        + str(newMovieLen)
        + ", language = '"
        + newMovieLanguage
        + "',  show_start = '"
        + startShowing
        + "', show_end = '"
        + endShowing
        + "' WHERE movie_id = "
        + str(movieID)
    )

    if res == []:
        subTypes = types.split(" ")
        while len(subTypes) < 3:
            subTypes.append("NUL")

        res = runQuery(
            "UPDATE types SET type1 = '"
            + subTypes[0]
            + "', type2 = '"
            + subTypes[1]
            + "', type3 = '"
            + subTypes[2]
            + "' WHERE movie_id = "
            + str(movieID)
        )
        if res == []:
            return "<h5>Thông tin phim được cập nhật thành công</h5>"
        else:
            print(res)
    else:
        print(res)
    return "<h5>Đã xảy ra lỗi</h5>"


# delete movie route
@app.route("/getMovieInfoForDelete", methods=["GET"])
def movieList1():
    res = runQuery("SELECT * FROM movies")

    return render_template("currentmovie1.html", movies=res)


@app.route("/deleteMovieInfo", methods=["POST"])
def deleteMovieInfo():
    movieID = request.form["movieID"]
    res = runQuery("DELETE FROM movies WHERE movie_id = " + str(movieID))
    if res == []:
        return "<h5>Đã xóa phim thành công</h5>"
    else:
        print(res)
    return "<h5>Đã xảy ra lỗi</h5>"


# Search movie route
@app.route("/searchMovieInfo", methods=["POST"])
def searchMovieInfo():
    searchMovieName = request.form["searchMovieName"]
    res = runQuery("SELECT * FROM movies WHERE movie_name = '" + searchMovieName + "'")
    if res == []:
        return "<h4>Không tìm thấy thông tin phim</h4>"

    return render_template("searchmovieinfo.html", movies=res)


# Route cho show
@app.route("/getShowOption", methods=["POST"])
def getShowOption():
    return render_template("showoption.html")


# Add Show
@app.route("/getValidMovies", methods=["POST"])
def validMovies():
    showDate = request.form["showDate"]

    res = runQuery(
        "SELECT movie_id,movie_name,length,language FROM movies WHERE show_start <= '"
        + showDate
        + "' and show_end >= '"
        + showDate
        + "'"
    )

    if res == []:
        return "<h5>Không có phim nào được chiếu trong khoảng thời gian này</h5>"

    movies = []

    for i in res:
        subTypes = runQuery("SELECT * FROM types WHERE movie_id = " + str(i[0]))

        t = subTypes[0][1]

        if subTypes[0][2] != "NUL":
            t = t + " " + subTypes[0][2]
        if subTypes[0][3] != "NUL":
            t = t + " " + subTypes[0][3]

        movies.append((i[0], i[1], t, i[2], i[3]))

    return render_template("validmovies.html", movies=movies)


@app.route("/getHallsAvailable", methods=["POST"])
def getHalls():
    movieID = request.form["movieID"]
    showDate = request.form["showDate"]
    showTime = request.form["showTime"]

    res = runQuery("SELECT length FROM movies WHERE movie_id = " + movieID)

    movieLen = res[0][0]

    showTime = int(showTime)

    showTime = int(showTime / 100) * 60 + (showTime % 100)

    endTime = showTime + movieLen

    res = runQuery(
        "SELECT hall_id, length, time FROM shows NATURAL JOIN movies WHERE Date = '"
        + showDate
        + "'"
    )

    unavailableHalls = set()

    for i in res:

        x = int(i[2] / 100) * 60 + (i[2] % 100)

        y = x + i[1]

        if x >= showTime and x <= endTime:
            unavailableHalls = unavailableHalls.union({i[0]})

        if y >= showTime and y <= endTime:
            unavailableHalls = unavailableHalls.union({i[0]})

    res = runQuery("SELECT DISTINCT hall_id FROM halls")

    availableHalls = set()

    for i in res:

        availableHalls = availableHalls.union({i[0]})

    availableHalls = availableHalls.difference(unavailableHalls)

    if availableHalls == set():

        return "<h5>Không có phòng chiếu trống tại thời điểm đó</h5>"

    return render_template("availablehalls.html", halls=availableHalls)


@app.route("/insertShow", methods=["POST"])
def insertShow():
    hallID = request.form["hallID"]
    movieID = request.form["movieID"]
    movieType = request.form["movieType"]
    showDate = request.form["showDate"]
    showTime = request.form["showTime"]

    showID = 0
    res = None

    while res != []:
        showID = randint(0, 2147483646)
        res = runQuery("SELECT show_id FROM shows WHERE show_id = " + str(showID))

    res = runQuery(
        "INSERT INTO shows VALUES("
        + str(showID)
        + ","
        + movieID
        + ","
        + hallID
        + ",'"
        + movieType
        + "',"
        + showTime
        + ",'"
        + showDate
        + "',"
        + "NULL"
        + ")"
    )

    print(res)

    if res == []:
        return (
            "<h5>Suất chiếu được thêm vào thành công</h5>\
		<h6>Mã suất chiếu: "
            + str(showID)
            + "</h6>"
        )

    else:
        print(res)
    return "<h5>Đã xảy ra lỗi</h5>"


# Alter Price
@app.route("/getPriceList", methods=["GET"])
def priceList():
    res = runQuery("SELECT * FROM price_listing ORDER BY type")

    sortedDays = [
        "Sunday",
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
    ]

    res = sorted(res, key=lambda x: sortedDays.index(x[2]))
    print(res)



    return render_template("currentprices.html", prices=res)


@app.route("/setNewPrice", methods=["POST"])
def setPrice():
    priceID = request.form["priceID"]
    newPrice = request.form["newPrice"]

    res = runQuery(
        "UPDATE price_listing SET price = "
        + str(newPrice)
        + " WHERE price_id = "
        + str(priceID)
    )

    if res == []:
        return (
            "<h5>Giá đã thay đổi thành công</h5>\
			<h6>Ghế Thường: "
            + newPrice
            + " VND</h6>\
			<h6>Ghế Vip: "
            + str(int(int(newPrice) * 1.5))
            + " VND</h6>"
        )

    else:
        print(res)
    return "<h5>Đã xảy ra lỗi</h5>"


# Route cho hall


# Route cho staff
# Add staff route
@app.route("/getStaffOption", methods=["POST"])
def getStaffOption():
    return render_template("staffoption.html")


@app.route("/fectchStaffInsertForm", methods=["GET"])
def getStaffForm():
    return render_template("staffform.html")


@app.route("/InsertStaff", methods=["POST"])
def insertStaff():
    staffName = request.form["staffName"]
    staffDob = request.form["staffDob"]
    staffGender = request.form["staffGender"]
    staffIDcard = request.form["staffIDcard"]
    staffPhoneNumber = request.form["staffPhoneNumber"]
    staffEmail = request.form["staffEmail"]
    staffAddress = request.form["staffAddress"]
    staffPosition = request.form["staffPosition"]
    staffSalary = request.form["staffSalary"]
    res = runQuery("SELECT * FROM nhan_vien")

    for i in res:
        if i[1] == staffName and i[4] == staffIDcard:
            return "<h5>Nhân viên này đã tồn tại</h5>"

    staffID = 0
    res = None

    while res != []:
        staffID = randint(0, 2147483646)
        res = runQuery(
            "SELECT ma_nhan_vien FROM nhan_vien WHERE ma_nhan_vien = " + str(staffID)
        )

    res = runQuery(
        "INSERT INTO nhan_vien VALUES("
        + str(staffID)
        + ",'"
        + staffName
        + "','"
        + staffDob
        + "','"
        + staffGender
        + "',"
        + str(staffIDcard)
        + ",'"
        + staffPosition
        + "',"
        + str(staffPhoneNumber)
        + ",'"
        + staffEmail
        + "','"
        + staffAddress
        + "','"
        + staffSalary
        + "')"
    )

    if res == []:
        print("Was able to add staff")
        if res == []:
            return (
                "<h5>Thông tin nhân viên đã được thêm thành công</h5>\
			<h6>Staff ID: "
                + str(staffID)
                + "</h6>"
            )
        else:
            print(res)
    else:
        print(res)

    return "<h5>Đã xảy ra lỗi</h5>"


# Update staff route
@app.route("/getStaffInfo", methods=["GET"])
def staffList():
    res = runQuery("SELECT * FROM nhan_vien")

    return render_template("currentstaff.html", staffs=res)


@app.route("/setNewStaffInfo", methods=["POST"])
def setStaffInfo():
    staffID = request.form["staffID"]
    newStaffName = request.form["newStaffName"]
    newStaffDob = request.form["newStaffDob"]
    newStaffGender = request.form["newStaffGender"]
    newStaffIDcard = request.form["newStaffIDcard"]
    newStaffPhoneNumber = request.form["newStaffPhoneNumber"]
    newStaffEmail = request.form["newStaffEmail"]
    newStaffAddress = request.form["newStaffAddress"]
    newStaffPosition = request.form["newStaffPosition"]
    newStaffSalary = request.form["newStaffSalary"]
    res = runQuery(
        "UPDATE nhan_vien SET ten_nhan_vien = '"
        + newStaffName
        + "', ngay_sinh = '"
        + newStaffDob
        + "', gioi_tinh = '"
        + newStaffGender
        + "', can_cuoc_cong_dan = "
        + str(newStaffIDcard)
        + ", chuc_vu = '"
        + newStaffPosition
        + "', so_dien_thoai = "
        + str(newStaffPhoneNumber)
        + ", email = '"
        + newStaffEmail
        + "', dia_chi = '"
        + newStaffAddress
        + "', luong = '"
        + newStaffSalary
        + "' WHERE ma_nhan_vien = "
        + str(staffID)
    )

    if res == []:
        return "<h5>Thông tin đã được cập nhật thành công</h5>"

    else:
        print(res)
    return "<h5>Đã xảy ra lỗi</h5>"


# Delete staff route
@app.route("/getStaffInfoForDelete", methods=["GET"])
def staffList1():
    res = runQuery("SELECT * FROM nhan_vien")

    return render_template("currentstaff1.html", staffs=res)


@app.route("/deleteStaffInfo", methods=["POST"])
def deleteStaffInfo():
    staffID = request.form["staffID"]
    res = runQuery("DELETE FROM nhan_vien WHERE ma_nhan_vien = " + str(staffID))
    if res == []:
        return "<h5>Thông tin đã được xóa thành công</h5>"
    else:
        print(res)
    return "<h5>Đã xảy ra lỗi</h5>"


# Show staff route
@app.route("/getStaffInfo1", methods=["GET"])
def staffList2():
    res = runQuery("SELECT * FROM nhan_vien")

    return render_template("currentstaff2.html", staffs=res)


@app.route("/showSelectedStaffInfo", methods=["POST"])
def showSelectedStaffInfo():
    staffID = request.form["staffID"]
    res = runQuery(
        "SELECT ma_nhan_vien,ten_nhan_vien,ngay_sinh,so_dien_thoai,email,dia_chi,chuc_vu,luong FROM nhan_vien WHERE ma_nhan_vien="
        + str(staffID)
    )

    staffs = []
    for i in res:
        staffs.append([i[0], i[1], i[2], i[3], i[4], i[5], i[6], i[7]])
    return render_template("showstaffinfo.html", staffs=staffs)


# Search staff route
@app.route("/searchStaffInfo", methods=["POST"])
def searchStaffInfo():
    searchStaffName = request.form["searchStaffName"]
    res = runQuery(
        "SELECT * FROM nhan_vien WHERE ten_nhan_vien = '" + searchStaffName + "'"
    )
    if res == []:
        return "<h4>Không tìm thấy nhân viên</h4>"

    return render_template("searchstaffinfo.html", staffs=res)


# Route cho member
# Add member route
@app.route("/getMemberOption", methods=["POST"])
def getMemberOption():
    return render_template("memberoption.html")


@app.route("/fectchMemberInsertForm", methods=["GET"])
def getMemberForm():
    return render_template("memberform.html")


@app.route("/InsertMember", methods=["POST"])
def insertMember():
    memberName = request.form["memberName"]
    memberDob = request.form["memberDob"]
    memberGender = request.form["memberGender"]
    memberIDcard = request.form["memberIDcard"]
    memberPhoneNumber = request.form["memberPhoneNumber"]
    memberEmail = request.form["memberEmail"]
    memberType = request.form["memberType"]
    res = runQuery("SELECT * FROM khach_hang")

    for i in res:
        if i[1] == memberName and i[4] == memberIDcard:
            return "<h5>Thông tin khách hàng đã tồn tại</h5>"

    memberID = 0
    res = None

    while res != []:
        memberID = randint(0, 2147483646)
        res = runQuery(
            "SELECT ma_khach_hang FROM khach_hang WHERE ma_khach_hang = "
            + str(memberID)
        )

    res = runQuery(
        "INSERT INTO khach_hang VALUES("
        + str(memberID)
        + ",'"
        + memberName
        + "','"
        + memberDob
        + "','"
        + memberGender
        + "',"
        + str(memberIDcard)
        + ","
        + str(memberPhoneNumber)
        + ",'"
        + memberEmail
        + "','"
        + memberType
        + "')"
    )

    if res == []:
        print("Was able to add member")
        if res == []:
            return (
                "<h5>Khách hàng đã được thêm vào thành công</h5>\
			<h6>Mã khách hàng: "
                + str(memberID)
                + "</h6>"
            )
        else:
            print(res)
    else:
        print(res)

    return "<h5>Đã xảy ra lỗi</h5>"


# Update member route
@app.route("/getMemberInfo", methods=["GET"])
def memberList():
    res = runQuery("SELECT * FROM khach_hang")

    return render_template("currentmember.html", members=res)


@app.route("/setNewMemberInfo", methods=["POST"])
def setMemberInfo():
    memberID = request.form["memberID"]
    newMemberName = request.form["newMemberName"]
    newMemberDob = request.form["newMemberDob"]
    newMemberGender = request.form["newMemberGender"]
    newMemberIDcard = request.form["newMemberIDcard"]
    newMemberPhoneNumber = request.form["newMemberPhoneNumber"]
    newMemberEmail = request.form["newMemberEmail"]
    newMemberType = request.form["newMemberType"]
    res = runQuery(
        "UPDATE khach_hang SET ten_khach_hang = '"
        + newMemberName
        + "', ngay_sinh = '"
        + newMemberDob
        + "', gioi_tinh = '"
        + newMemberGender
        + "', can_cuoc_cong_dan = "
        + str(newMemberIDcard)
        + ", so_dien_thoai = "
        + str(newMemberPhoneNumber)
        + ", email = '"
        + newMemberEmail
        + "', loai_khach_hang = '"
        + newMemberType
        + "' WHERE ma_khach_hang = "
        + str(memberID)
    )

    if res == []:
        return "<h5>Thông tin đã được cập nhật thành công</h5>"

    else:
        print(res)
    return "<h5>Đã xảy ra lỗi</h5>"


# Delete member route
@app.route("/getMemberInfoForDelete", methods=["GET"])
def memberList1():
    res = runQuery("SELECT * FROM khach_hang")

    return render_template("currentmember1.html", members=res)


@app.route("/deleteMemberInfo", methods=["POST"])
def deleteMemberInfo():
    memberID = request.form["memberID"]
    res = runQuery("DELETE FROM khach_hang WHERE ma_khach_hang = " + str(memberID))
    if res == []:
        return "<h5>Thông tin đã được xóa thành công</h5>"
    else:
        print(res)
    return "<h5>Đã xảy ra lỗi</h5>"


# Search member route
@app.route("/searchMemberInfo", methods=["POST"])
def searchMemberInfo():
    searchMemberName = request.form["searchMemberName"]
    res = runQuery(
        "SELECT * FROM khach_hang WHERE ten_khach_hang = '" + searchMemberName + "'"
    )
    if res == []:
        return "<h4>Không tìm thấy thông tin khách hàng</h4>"

    return render_template("searchmemberinfo.html", members=res)


# Search Route
@app.route("/getSearchOption", methods=["POST"])
def getSearchOption():
    return render_template("searchoption.html")


# Statistic Route
@app.route("/getStatisticOption", methods=["POST"])
def getStaisticOption():
    return render_template("statisticoption.html")


# View Booked Ticket On Show


@app.route("/getShowsShowingOnDate", methods=["POST"])
def getShowsOnDate():
    date = request.form["date"]

    res = runQuery(
        "SELECT show_id,movie_name,type,time FROM shows NATURAL JOIN movies WHERE Date = '"
        + date
        + "'"
    )

    if res == []:
        return "<h4>Không có suất chiếu nào trong khoảng thời gian này</h4>"
    else:
        shows = []
        for i in res:
            x = i[3] % 100
            if i[3] % 100 == 0:
                x = "00"
            shows.append([i[0], i[1], i[2], int(i[3] / 100), x])

        return render_template("shows.html", shows=shows)


@app.route("/getBookedWithShowID", methods=["POST"])
def getBookedTickets():
    showID = request.form["showID"]

    res = runQuery(
        "SELECT ticket_no,seat_no FROM booked_tickets WHERE show_id = "
        + showID
        + " order by seat_no"
    )

    if res == []:
        return "<h5>Chưa có vé đặt</h5>"

    tickets = []
    for i in res:
        if i[1] > 1000:
            tickets.append([i[0], i[1] - 1000, "Gold"])
        else:
            tickets.append([i[0], i[1], "Standard"])

    return render_template("bookedtickets.html", tickets=tickets)


# Route sql connection
def runQuery(query):
    try:
        db = mysql.connector.connect(
            host="localhost", database="db_theatre", user="sang", password="sang"
        )

        if db.is_connected():
            print("Connected to MySQL, running query: ", query)
            cursor = db.cursor(buffered=True)
            cursor.execute(query)
            db.commit()
            res = None
            try:
                res = cursor.fetchall()
            except Exception as e:
                print("Query returned nothing, ", e)
                return []
            return res

    except Exception as e:
        print(e)
        return e

    finally:
        db.close()

    print("Couldn't connect to MySQL")
    # Couldn't connect to MySQL
    return None


if __name__ == "__main__":
    app.run(host="0.0.0.0")
