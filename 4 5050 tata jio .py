<?php
// Check if the request is for the playlist
if ($_SERVER['REQUEST_URI'] == '/playlist') {
    // Get user IP and port
    $user_ip = !empty($_SERVER['REMOTE_ADDR']) ? $_SERVER['REMOTE_ADDR'] : 'localhost';
    $user_port = $_SERVER['SERVER_PORT'];
    
    // Define the playlist content
    $playlist_content = "#EXTM3U\n";
    $playlist_content .= "#EXTINF:-1 tvg-id=\"14597\" tvg-logo=\"\" group-title=\"ENGLISH CA\",AQUARIUM 4K\n";
    $playlist_content .= "$user_ip:$user_port/stream/14597\n";
    $playlist_content .= "#EXTINF:-1 tvg-id=\"10770\" tvg-logo=\"\" group-title=\"ENGLISH CA\",FIREPLACE TV 4K\n";
    $playlist_content .= "$user_ip:$user_port/stream/10770\n";
    $playlist_content .= "#EXTINF:-1 tvg-id=\"3\" tvg-logo=\"http://jiotv.be/stalker_portal/misc/logos/320/3.png\" group-title=\"ENGLISH CA\",GLOBAL 4K cc\n";
    $playlist_content .= "$user_ip:$user_port/stream/3\n";
    $playlist_content .= "#EXTINF:-1 tvg-id=\"6\" tvg-logo=\"\" group-title=\"ENGLISH CA\",OMNI 1 4K cc\n";
    $playlist_content .= "$user_ip:$user_port/stream/6\n";
    $playlist_content .= "#EXTINF:-1 tvg-id=\"10\" tvg-logo=\"\" group-title=\"ENGLISH CA\",CBC TORONTO 4K cc\n";
    $playlist_content .= "$user_ip:$user_port/stream/10\n";
    
    // Save the playlist content to a file
    file_put_contents('playlist.m3u', $playlist_content);
    
    // Serve the playlist file
    header('Content-Type: audio/x-mpegurl');
    header('Content-Disposition: attachment; filename="playlist.m3u"');
    echo $playlist_content;
    exit;
}

// Original code starts here
$id = @$_GET['id'];
$user_ip = $_SERVER['REMOTE_ADDR'];
$currentTimestamp = time();
$portal = "new.jiotv.be";
$mac = "00:1A:79:97:55:B9";
$deviceid = "B8F453DCDAEE02318C9FA912D9E409EE96B75AE592A70B526AA84478533C0A66";
$deviceid2 = "B8F453DCDAEE02318C9FA912D9E409EE96B75AE592A70B526AA84478533C0A66";
$serial = "500482917046B";
$sig = "";
$n1 = "http://$portal/stalker_portal/server/load.php?type=stb&action=handshake&prehash=false&JsHttpRequest=1-xml";
$h1 = [ 
    "Cookie: mac=$mac; stb_lang=en; timezone=GMT", 
    "X-Forwarded-For: $user_ip", 
    "Referer: http://$portal/stalker_portal/c/", 
    "User-Agent: Mozilla/5.0 (QtEmbedded; U; Linux; C) AppleWebKit/533.3 (KHTML, like Gecko) MAG200 stbapp ver: 2 rev: 250 Safari/533.3", 
    "X-User-Agent: Model: MAG250; Link:", 
];
$c1_curl = curl_init();
curl_setopt($c1_curl, CURLOPT_URL, $n1);
curl_setopt($c1_curl, CURLOPT_SSL_VERIFYHOST, false);
curl_setopt($c1_curl, CURLOPT_SSL_VERIFYPEER, false);
curl_setopt($c1_curl, CURLOPT_RETURNTRANSFER, true);
curl_setopt($c1_curl, CURLOPT_HTTPHEADER, $h1);
curl_setopt($c1_curl, CURLOPT_USERAGENT, 'Mozilla/5.0 (QtEmbedded; U; Linux; C) AppleWebKit/533.3 (KHTML, like Gecko) MAG200 stbapp ver: 2 rev: 250 Safari/533.3');
$res1 = curl_exec($c1_curl);
curl_close($c1_curl);
$response = json_decode($res1, true);
$token = $response['js']['random'];
$real = $response['js']['token'];
$bearer_token = $real ?? ""; // Fetch the token dynamically
$h2 = [
    "Cookie: mac=$mac; stb_lang=en; timezone=GMT",
    "X-Forwarded-For: $user_ip",
    "Authorization: Bearer $bearer_token",
    "Referer: http://$portal/stalker_portal/c/",
    "User-Agent: Mozilla/5.0 (QtEmbedded; U; Linux; C) AppleWebKit/533.3 (KHTML, like Gecko) MAG200 stbapp ver: 2 rev: 250 Safari/533.3",
    "X-User-Agent: Model: MAG250; Link:",
];
$n2 = "http://$portal/stalker_portal/server/load.php?type=stb&action=get_profile&hd=1&ver=ImageDescription: 0.2.18-r14-pub-250; ImageDate: Fri Jan 15 15:20:44 EET 2016; PORTAL version: 5.5.0; API Version: JS API version: 328; STB API version: 134; Player Engine version: 0x566&num_banks=2&sn=$serial&stb_type=MAG254&image_version=218&video_out=hdmi&device_id=$deviceid&device_id2=$deviceid2&signature=$sig&auth_second_step=1&hw_version=1.7-BD-00&not_valid_token=0&client_type=STB&hw_version_2=7c431b0aec69b2f0194c0680c32fe4e3&timestamp=$currentTimestamp&api_signature=263&metrics={\"mac\":\"$mac\",\"sn\":\"$serial\",\"model\":\"MAG254\",\"type\":\"STB\",\"uid\":\"$deviceid\",\"random\":\"$token\"}&JsHttpRequest=1-xml";
$c2_curl = curl_init();
curl_setopt($c2_curl, CURLOPT_URL, $n2);
curl_setopt($c2_curl, CURLOPT_SSL_VERIFYHOST, false);
curl_setopt($c2_curl, CURLOPT_SSL_VERIFYPEER, false);
curl_setopt($c2_curl, CURLOPT_RETURNTRANSFER, true);
curl_setopt($c2_curl, CURLOPT_HTTPHEADER, $h2);
curl_setopt($c2_curl, CURLOPT_USERAGENT, 'Mozilla/5.0 (QtEmbedded; U; Linux; C) AppleWebKit/533.3 (KHTML, like Gecko) MAG200 stbapp ver: 2 rev: 250 Safari/533.3');
$res2 = curl_exec($c2_curl);
curl_close($c2_curl);
$n3 = "http://$portal/stalker_portal/server/load.php?type=itv&action=create_link&cmd=ffrt%http://localhost/ch/$id&JsHttpRequest=1-xml";
$c3_curl = curl_init();
curl_setopt($c3_curl, CURLOPT_URL, $n3);
curl_setopt($c3_curl, CURLOPT_SSL_VERIFYHOST, false);
curl_setopt($c3_curl, CURLOPT_SSL_VERIFYPEER, false);
curl_setopt($c3_curl, CURLOPT_RETURNTRANSFER, true);
curl_setopt($c3_curl, CURLOPT_HTTPHEADER, $h2);
curl_setopt($c3_curl, CURLOPT_USERAGENT, 'Mozilla/5.0 (QtEmbedded; U; Linux; C) AppleWebKit/533.3 (KHTML, like Gecko) MAG200 stbapp ver: 2 rev: 250 Safari/533.3');
$res3 = curl_exec($c3_curl);
curl_close($c3_curl);
$i6 = json_decode($res3, true);
$d7 = $i6["js"]["cmd"];
header("Location: " . $d7);
die;
