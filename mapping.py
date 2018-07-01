# -*- coding:utf-8 -*-
import pandas as pd
import os
import collections
import re


def write_to_csv(mapping_df, output_path):
    if not os.path.isfile(output_path):
        mapping_df.to_csv(output_path, encoding='utf8', mode='w', header=True, index=False)
    else:
        mapping_df.to_csv(output_path, encoding='utf8', mode='a', header=False, index=False)


class Mapping:

    def __init__(self, rule, brand_name_origin):
        self.rule = rule
        self.brand_name_origin = brand_name_origin

    @property
    def rule(self):
        return self._rule

    @rule.setter
    def rule(self, value):
        if not isinstance(value, pd.DataFrame):
            raise ValueError("Rule must be a DataFrame")
        if 'include' not in value.columns:
            raise ValueError("No include column")
        if 'equal' not in value.columns:
            raise ValueError("No equal column")
        if 'exclude' not in value.columns:
            raise ValueError("No exclude column")
        if 'output' not in value.columns:
            raise ValueError("No output column")
        self._rule = value.fillna('')

    @property
    def brand_name_origin(self):
        return self._brand_name_origin

    @brand_name_origin.setter
    def brand_name_origin(self, value):
        if isinstance(value, str):
            raise ValueError("Standard brand name must be iterable and cannot be a string")
        if not isinstance(value, collections.Iterable):
            raise ValueError("Standard brand name must be iterable")
        if not all([isinstance(item, str) for item in value]):
             raise ValueError("All brandname should be string")
        self._brand_name_origin = value

    @staticmethod
    def _re_match(include, no_space_name):
        include_pattern = re.compile(include)
        return bool(include_pattern.search(no_space_name))

    # remove bracket (a) => a in case rule like (a)&(b)
    @staticmethod
    def _extract_group(group):
        result_group = ''
        rule_in_group = re.findall(r'\((.*?)\)', group)
        if len(rule_in_group) > 0:
            result_group = rule_in_group[0]
        else:
            result_group = group
        return result_group

    def _get_rule(self, row):
        # a|b&c|d => ['a|b', 'c|d']
        # extract: remove bracket
        rule_include = [self._extract_group(n) for n in row['include'].split('&')]
        # a|b => ['a', 'b']
        rule_equal = [self._extract_group(n) for n in row['exclude'].split('|')]
        # a&b&c => ['a', 'b', 'c']
        rule_exclude = [self._extract_group(n) for n in row['exclude'].split('&')]
        return {'rule_include': rule_include, 'rule_equal': rule_equal, 'rule_exclude': rule_exclude,
                'output': row['output']}

    # match all brandnama with a rule
    def match_mapping(self, rule):
        brandsname = self._brand_name_origin
        # include rule
        rule_include = rule['rule_include']
        # equal rule
        rule_equal = rule['rule_equal']
        # exclude rule
        rule_exclude = rule['rule_exclude']
        # mapping result
        output = rule['output']
        match_list = []
        for name in brandsname:
            if type(name) != str:
                continue
            # remove all space from brandname
            no_space_name = name.replace(" ", "")
            result_include = all(
                [self._re_match(include.replace(" ", "").lower(), no_space_name.lower()) for include in rule_include])
            result_equal = all([equal.replace(" ", "").lower() == no_space_name.lower() for equal in rule_equal])
            result_exclude = True
            if len(rule_exclude) >= 1 and rule_exclude[0] != '':
                result_exclude = all(
                    [not self._re_match(exclude.replace(" ", "").lower(), no_space_name.lower()) for exclude in rule_exclude])
            result = (result_include or result_equal) and result_exclude
            if result:
                match_list.append({"origin_brandname": name, "brandname": output})
        return match_list

    def mapping_content(self):
        rule_group = self.rule
        result = []
        for index, row in rule_group.iterrows():
            # split rule to regex part e.g. include: a|b&c|d => ['a|b', 'c|d']
            rule = self._get_rule(row)
            # match brand name with rule
            match_result = self.match_mapping(rule)
            if len(match_result) > 0:
                result += match_result
        mapping_full_result = pd.DataFrame(result).drop_duplicates()
        return mapping_full_result

    def get_mapping_result(self, df_result):
        grouped = df_result.groupby(['origin_brandname'])
        # single match
        ready_result = grouped.filter(lambda x: x['origin_brandname'].agg(['count']) == 1)
        # multi match
        confuse_result = grouped.filter(lambda x: x['origin_brandname'].agg(['count']) > 1)
        mapped_origin_brands = df_result['origin_brandname']
        # no match
        no_mapped_brands = pd.DataFrame({'name_origin': list(set(self.brand_name_origin) - set(mapped_origin_brands))})
        return ready_result, confuse_result, no_mapped_brands

    def all_result_to_csv(self, single_match_path, multi_match_path, no_match_path):
        mapping_result_df = self.mapping_content()
        single_match, multi_match, no_match = self.get_mapping_result(mapping_result_df)
        single_match.to_csv(single_match_path, encoding='utf8', mode='w', header=True, index=False)
        multi_match.to_csv(multi_match_path, encoding='utf8', mode='w', header=True, index=False)
        no_match.to_csv(no_match_path, encoding='utf8', mode='w', header=True, index=False)
        return single_match, multi_match, no_match


def main():
    dirname = os.path.dirname(__file__)
    rule_path = os.path.join(dirname, 'test_file/mapping_rule.csv')
    brand_origin_path = os.path.join(dirname, 'test_file/brand_name_origin.csv')
    single_match_path = os.path.join(dirname, 'test_file/mapping_result/single_match_result.csv')
    multi_match_path = os.path.join(dirname, 'test_file/mapping_result/multi_match_result.csv')
    no_match_path = os.path.join(dirname, 'test_file/mapping_result/no_match_result.csv')
    rule_set = pd.read_csv(rule_path)
    brand_name_origin = pd.read_csv(brand_origin_path)['name_origin']
    mapping = Mapping(rule_set, brand_name_origin)
    mapping.all_result_to_csv(single_match_path, multi_match_path, no_match_path)


if __name__ == '__main__':
    main()
