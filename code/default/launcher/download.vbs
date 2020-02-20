Sub DownloadFile(url, strPath)
    dim xHttp: Set xHttp = createobject("Microsoft.XMLHTTP")
    dim bStrm: Set bStrm = createobject("Adodb.Stream")
    xHttp.Open "GET", url, False
    xHttp.Send

    with bStrm
        .type = 1 '//binary
        .open
        .write xHttp.responseBody
        .savetofile strPath, 2 '//overwrite
    end with

End Sub
