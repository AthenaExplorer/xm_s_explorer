from datetime import date, datetime, timedelta

from xm_s_common.raw_sql import exec_sql
from .frequent import fix_dimension


def fix_data():
    start_date = date(2020, 10, 15)
    while start_date < date(2021, 4, 21):
        if start_date == date(2020, 10, 15):
            sql_query_base = "SELECT msg_value FROM xm_s_explorer.value WHERE date=%s; "
            base_val = exec_sql(sql_query_base, (start_date,))[0][0]
            sql_update_base = "UPDATE xm_s_explorer.fad_scores SET ref_data =%s where day =%s and tag=1 and sub_dimension_id=9;"
            exec_sql(sql_update_base, (base_val, start_date))
        sql_query_base = "SELECT msg_value FROM xm_s_explorer.value WHERE date=%s; "
        val = exec_sql(sql_query_base, (start_date,))[0][0]
        sql_check = "SELECT * FROM xm_s_explorer.fad_scores WHERE tag = 0 and day = %s and sub_dimension_id=9 "
        res = exec_sql(sql_check, (start_date,))
        if res:
            sql_update_real = "UPDATE xm_s_explorer.fad_scores SET weighting_factor=1, ref_data=%s, real_time_data=%s, " \
                              "basic_scores=%s, weighing_scores=%s where day =%s and tag=0 and sub_dimension_id=9  ;"
            exec_sql(sql_update_real, (base_val, val, val / base_val, val / base_val, start_date))
        else:
            sql_insert_new = "INSERT INTO xm_s_explorer.fad_scores(weighting_factor, ref_data, real_time_data, basic_scores, " \
                             "weighing_scores, `day`, create_time, tag, sub_dimension_id)VALUES(1, %s, %s, %s, %s, %s, %s, 0, 9);"
            exec_sql(sql_insert_new, (base_val, val, val / base_val, val / base_val, start_date,
                                      datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0)))
        start_date += timedelta(days=1)
    fix_dimension()
