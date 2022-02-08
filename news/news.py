import re
import os
 import nltk
import html as ht
import numpy as np
import pandas as pd
from newsfeed.news.db.events import *
from newsfeed.news.db.gkg import *
from newsfeed.utils import fulltext as ft

nltk.download("punkt")


class NewsSource(object):

    def __init__(self,
                 start_date: str = "2021-01-01-00-00-00",
                 enddate: str = "2021-01-02-00-00-00",
                 date=None,
                 event: bool = False):
        __BASE_DIR__ = os.path.dirname(os.path.abspath(__file__))
        self.__FIPS_DIR__ = os.path.join(__BASE_DIR__,
                                         "FIPS_country_codes.csv")
        self.QuadClass={1:"Verbal Cooperation", 2:"Material Cooperation", 3:"Verbal Conflict", 4:"Material Conflict"}
        self.start_date = start_date
        self.end_date = enddate

        gdelt_events_v2_events = EventV2(start_date="2021-01-01-00-00-00",
                                         end_date="2021-01-02-00-00-00")
        gdelt_events_v2_mentions = EventV2(start_date="2021-01-01-00-00-00",
                                           end_date="2021-01-02-00-00-00",
                                           table="mentions")
        gdelt_events_v2_gkg = GKGV2(start_date="2021-01-01-00-00-00",
                                    end_date="2021-01-02-00-00-00")
        if date != None:
            if event:
                self.events_nowtime = gdelt_events_v2_events.query_nowtime(date=date)
                self.mentions_nowtime = gdelt_events_v2_mentions.query_nowtime(date=date)
            else:
                self.gkg_nowtime = gdelt_events_v2_gkg.query_nowtime(date=date)
        else:
            if event:
                self.events_nowtime = gdelt_events_v2_events.query_nowtime()
                self.mentions_nowtime = gdelt_events_v2_mentions.query_nowtime()
            else:
                self.gkg_nowtime = gdelt_events_v2_gkg.query_nowtime()

        self.country_code = pd.read_csv(self.__FIPS_DIR__)

    def extract_country(self, text=None):
        for i in range(0, len(self.country_code)):
            name, code_fips = self.country_code["Name"][i], str(
                self.country_code["Code_FIPS"][i])
            if type(text) != str:
                return "worldwide"
            else:
                if name in text or code_fips in text in text:
                    return name

    def extract_xml(self, xml: str = None):
        reg_title = re.compile('<PAGE_TITLE>(.*?)<\/PAGE_TITLE>')
        #reg_links = re.compile('<PAGE_LINKS>(.*?)<\/PAGE_LINKS>')
        #reg_author = re.compile('<PAGE_AUTHORS>(.*?)<\/PAGE_AUTHORS>')
        xml_info = {
            "title": ht.unescape(reg_title.findall(xml)[0])
            #"related_url": reg_links.findall(xml),
            #"Authors": reg_author.findall(xml)
        }
        return xml_info

    def extract_news(self, url: str = None):
        if url is None:
            return np.nan, np.nan
        else:
            try:
                article = ft.download(url=url)
                article.nlp()
                title, summary = article.title, article.summary
                if title == "":
                    return np.nan, np.nan
                else:
                    return title, summary
            except Exception as e:
                return np.nan, np.nan

    def Articles(self):
        self.gkg_nowtime = self.gkg_nowtime.sample(10)
        articles = pd.DataFrame({
            "country_info":
            self.gkg_nowtime["V2ENHANCEDLOCATIONS"].apply(
                self.extract_country),
            "article_info":
            self.gkg_nowtime["V2EXTRASXML"].apply(self.extract_xml),
            "source":
            self.gkg_nowtime["V2SOURCECOMMONNAME"],
            "url":
            self.gkg_nowtime["V2DOCUMENTIDENTIFIER"]
        })
        return articles

    def Events(self):
        intersection_list = list(
            set(self.events_nowtime["GLOBALEVENTID"]).intersection(
                set(self.mentions_nowtime["GLOBALEVENTID"])))
        intersection_df = pd.merge_asof(
            self.events_nowtime[self.events_nowtime["GLOBALEVENTID"].isin(
                intersection_list)],
            self.mentions_nowtime[self.mentions_nowtime["GLOBALEVENTID"].isin(
                intersection_list)],
            on="GLOBALEVENTID",
            direction="nearest")

        query_columns = [
            "GLOBALEVENTID", "QuadClass", #"Actor1CountryCode", "Actor2CountryCode",
            "DATEADDED", "SOURCEURL", "QuadClass", "GoldsteinScale",
            "NumArticles", "AvgTone", "Mentionidentifier",
            "Confidence"
        ]

        intersection_df.drop_duplicates(subset="SOURCEURL", inplace=True)
        intersection_df = intersection_df[query_columns].reset_index(
            drop=True).sort_values("AvgTone")
        intersection_df_down, intersection_df_up = intersection_df.head(
        ).sort_values("GoldsteinScale"), intersection_df.tail().sort_values(
            "GoldsteinScale")
        intersection_df_down["title"], intersection_df_down["summary"] = zip(*intersection_df_down["SOURCEURL"].apply(self.extract_news))
        intersection_df_up["title"], intersection_df_up["summary"]  = zip(*intersection_df_up["SOURCEURL"].apply(self.extract_news))

        return intersection_df_down[intersection_df_down["title"].notna()], intersection_df_up[intersection_df_up["title"].notna()]