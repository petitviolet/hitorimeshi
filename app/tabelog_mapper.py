# -*- encoding:utf-8 -*-
'''使わない'''
import MySQLdb
import json
from urllib2 import urlopen
from Table import *
from secrete import *

API_KEY = open('../api_key.txt', 'r').read().strip()
JSON_TAGNAMES = ['Rcd', 'RestaurantName', 'TabelogMobileUrl', 'TotalScore', \
'Situation', 'DinnerPrice', 'LunchPrice', 'Category', 'Station', 'Address', \
'Tel', 'BusinessHours', 'Holiday', 'Latitude', 'Longitude', 'Point', 'len']
RADIUS = 6371
margin = 0.2

def geo_coding(landmark):
    url = 'http://maps.googleapis.com/maps/api/geocode/json?address={landmark}&sensor=true'
    geo_json = json.load(urlopen(url.format(landmark=landmark)))
    latlng = geo_json['results'][0]['geometry']['location']
    result = {'latitude':latlng['lat'], 'longitude':latlng['lng']}
    return result


class Tabelog_Mapper(object):
    def __init__(self, landmark=None, latitude=None, longitude=None, margin=0.1):
        self.con = MySQLdb.connect(db=db, host=host,\
                user=user, passwd=passwd, charset=charset)
        self.cur = self.con.cursor(MySQLdb.cursors.DictCursor)
        self.landmark = landmark
        self.margin = margin
        if landmark and latitude and longitude:
            raise ValueError('ランドマークか緯度経度のどちらか')
        if not landmark and (latitude or longitude):
            raise ValueError('インスタンス作成時にランドマークか緯度経度を指定してください')
        elif landmark and (not latitude or not longitude):
            latlng = geo_coding(landmark)
            self.latitude = latlng['latitude']
            self.longitude = latlng['longitude']
        else:
            self.latitude = latitude
            self.longitude = longitude

    def __del__(self):
        self.cur.close()
        self.con.close()

    def order_by_near_point(self):
        '''DBから、self.latitudeとself.longitudeに近い店を取得する
        jsonで返す
        '''
        sql = ("select Rcd, RestaurantName, TabelogMobileUrl, TotalScore, "
        "Situation, DinnerPrice, LunchPrice, Category, Station, Address, Tel,"
        "BusinessHours, Holiday, "
        "X(LatLng) as Latitude, Y(LatLng) as Longitude, AsText(LatLng) as Point,"
        "GLength(GeomFromText("
        "Concat('LineString({lng} {lat},', X(LatLng), ' ', Y(LatLng), ')'))) as len "
        "from tabelog where MBRContains(GeomFromText("
        "'LineString({lng2} {lat2}, {lng3} {lat3})'), LatLng) order by len;")\
        .format(lat = self.latitude, lng = self.longitude,\
                lat2 = self.latitude + margin, lng2 = self.longitude + margin,\
                lat3 = self.latitude - margin, lng3 = self.longitude - margin)
        count = self.cur.execute(sql)
        results = self.cur.fetchall()
        # results_list= []
        # for result in results:
        #     result_dic = {}
        #     for k, v in izip(JSON_TAGNAMES, result):
        #         result_dic[k] = v
        #     results_list.append(result_dic)
        # results_json = json.dumps(results_list, sort_keys=True)
        results_json = json.dumps(results, sort_keys=True)
        return count, results_json

    def more_info_of_restaurant(self, rcd):
        '''rcdでその店のより詳細な情報を取得
        '''
        sql = 'select * from tabelog where rcd = {rcd}'
        self.cur.execute(sql.format(rcd = rcd))
        result = self.cur.fetchall()
        return json.dumps(result[0], sort_keys=True)
