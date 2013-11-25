ぼっち飯図鑑のサーバサイドAPI  
==

更新日時
--
2013/11/25 14:13  
1. /postで取得した称号の名前を返すようにした


使い方
--
* 基本となるURLは秘密です
* Basic認証をかけています
* 返り値はjson形式\(key: value\)です


TODO
--

1.必要なapiを作成する（画面が出来てきたら分かってくるはず）

2.作成済みのapiの改良（必要に合わせて）

### レストラン
1.近隣の店舗検索
  * url: /near\_rst
  * method: post
  * data: \{zoom: ズームレベル, lat: 緯度, lng: 経度, limit: 取得数(デフォルトで100件)\}
  * 返り値: \{result: \{rst\_id, Restaurantname, Category, lat, lng, distance, difficulty\(四捨五入\), raw\_difficulty\}\}

2.店舗の詳細情報
  * url: /read\_rst
  * method: post
  * data: \{rst\_id: tabelogテーブルのrcd\}
  * 返り値: \{rst\_id, restaurantname, tabelogmoblieurl, totalscore,  
  situation, dinnerprice, lunchprice, category, station, address,  
  tel, buisinesshours, holiday, lat, lng, difficluty, raw\_difficulty\}

### User
1.ユーザー作成
  * url: /create\_user
  * method: post
  * data: \{name: ユーザーの名前, home: お気に入り？の場所\}
  * 返り値: \{user\_id: 作成されたuserのid\}

2.ユーザー情報取得
  * url: /read\_user
  * method: post
  * data: \{user\_id: ユーザーid\}
  * 返り値: \{result: \{id, user\_name, home\_place\}\}

3.ユーザー情報更新
  * url: /update\_user
  * method: put
  * data: \{user\_id: ユーザーid, new\_name: 新しい名前, new\_home: 新しい場所\}
  * 返り値: \{update: 成功\(True\) or 失敗\(False\)\}

4.ユーザー削除
  * url: /delete\_user
  * method: delete
  * data: \{user\_id: ユーザーid, confirmation: 削除確認\(True or False\)\}
  * 返り値: \{delete: 成功\(True\) or 失敗\(False\)\}

### UserPost
1.作成or更新
  * url: /post
  * method: post
  * data: \{user\_id: ユーザーid, rst\_id: tabelogテーブルのrcd\(idではない\),  
                                            difficulty: 難易度, comment: コメント\}
  * 返り値: \{acquired\_titles: 取得済み称号の名前\}

  * 返り値: \{user\_post\_id: 作成or更新されたuser\_postのid\}

2.情報取得
  * url: /read\_post
  * method: post
  * data: \{user\_id: ユーザーid, rst\_id: レストランのrcd\}
  * 返り値: \{user\_post: \{user\_id, rst\_id, difficulty, comment\}\}

3.削除
  * url: /delete\_post
  * method: delete
  * data: \{user\_id: ユーザーid, rst\_id: レストランのrcd\}
  * 返り値: \{delete\_user\_post: 成功\(True\) or 失敗\(False\)\}
  
