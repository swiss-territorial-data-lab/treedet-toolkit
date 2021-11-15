import numpy as np
import pygeohash as pgh
import pandas as pd
import geopandas as gpd
import networkx as nx

from collections import OrderedDict
from scipy.spatial import cKDTree
from fractions import Fraction

def geohash(row):
    out = pgh.encode(latitude=row.geometry.y, longitude=row.geometry.x, precision=16)
    return out


# cf. https://gis.stackexchange.com/questions/222315/geopandas-find-nearest-point-in-other-dataframe
def ckdnearest(gdA, gdB):

    assert 'geohash' in gdA.columns.tolist()
    assert 'geohash' in gdB.columns.tolist()

    _gdA = gdA.rename(columns={'geohash': 'geohash_A'})
    _gdB = gdB.rename(columns={'geohash': 'geohash_B'})

    nA = np.array(list(_gdA.geometry.apply(lambda x: (x.x, x.y))))
    nB = np.array(list(_gdB.geometry.apply(lambda x: (x.x, x.y))))
    
    btree = cKDTree(nB)
    dist, idx = btree.query(nA, k=1)
    
    gdB_nearest = _gdB.iloc[idx].drop(columns=["geometry"]).reset_index(drop=True)
    
    gdf = pd.concat(
        [
            _gdA.reset_index(drop=True),
            gdB_nearest,
            pd.Series(dist, name='dist')
        ], 
        axis=1)

    return gdf


def clip(gdf, sectors):
    
    clipped_gdf = gpd.GeoDataFrame()
    for _, sector in sectors.iterrows():
        tmp = gpd.clip(gdf, sector.geometry).copy()
        tmp['sector'] = sector.sector
        clipped_gdf = pd.concat([clipped_gdf, tmp])

    return clipped_gdf


def legacy_tag(gt, preds, tol):

    assert 'geohash' in gt.columns.tolist()
    assert 'geohash' in preds.columns.tolist()

    _gt = gt.copy()
    _preds = preds.copy()

    # gt -> preds => TP, FN
    gt_vs_preds = ckdnearest(_gt, _preds)
    matches = gt_vs_preds[gt_vs_preds.dist <= tol] # GT objects which are also found in preds
    # ---

    ## init
    _gt['tag'] = 'FN'
    ## proper tagging
    _gt.loc[_gt.geohash.isin(matches.geohash_A.values), 'tag'] = 'TP'
   
    # preds -> gt => TP, FP 
    ## init
    _preds['tag'] = 'FP'
    ## proper tagging
    _preds.loc[ _preds.geohash.isin(matches.geohash_B.values), 'tag' ] = 'TP'

    try:
        assert len(_preds[_preds.tag == 'TP']) == len(_gt[_gt.tag == 'TP']), f"{len(_preds[_preds.tag == 'TP'])} != {len(_gt[_gt.tag == 'TP'])}"
    except AssertionError as e:
        print(f"AssertionError: {e}")

    return _gt, _preds


def tag(gt, dets, tol_m, gt_prefix, dets_prefix):
    """
        - tol_m = tolerance in meters
    """

    ### --- helper functions --- ###
    def make_groups():

        g = nx.Graph()
        for row in l_join[l_join.geohash_y.notnull()].itertuples():
            g.add_edge(row.geohash_x, row.geohash_y)

        groups = list(nx.connected_components(g))

        return groups


    def assess_group(group):

        # init
        cnt_gt = 0
        cnt_dets = 0
        FP_charge = 0
        FN_charge = 0
    
        for el in group:
            if el.startswith(dets_prefix):
                cnt_dets += 1
            if el.startswith(gt_prefix):
                cnt_gt += 1
            
        if cnt_dets > cnt_gt:
            FP_charge = cnt_dets - cnt_gt
        
        if cnt_dets < cnt_gt:
            FN_charge = cnt_gt - cnt_dets

        return dict(cnt_gt=cnt_gt, cnt_dets=cnt_dets, FP_charge=FP_charge, FN_charge=FN_charge)


    def assign_groups(row):

        group_index = {node: i for i, group in enumerate(groups) for node in group}
    
        try:
            row['group_id'] = group_index[row['geohash']]
        except: 
            row['group_id'] = None
        
        return row


    def assign_charges(row):
        
        for k, v in charges_dict[row['geohash']].items():
            row[k] = v

        return row

    ### --- main --- ###
    assert 'geohash' in gt.columns.tolist()
    assert 'geohash' in dets.columns.tolist()

    # init
    _gt = gt.copy()
    _dets = dets.copy()
    _dets['geometry'] = _dets.geometry.buffer(tol_m)

    charges_dict = {}

    # spatial joins
    l_join = gpd.sjoin(_dets, _gt, how='left', predicate='intersects', lsuffix='x', rsuffix='y')
    r_join = gpd.sjoin(_dets, _gt, how='right', predicate='intersects', lsuffix='x', rsuffix='y')

    # trivial False Positives
    trivial_FPs = l_join[l_join.geohash_y.isna()]
    for tup in trivial_FPs.itertuples():
        charges_dict = {
            **charges_dict,
            tup.geohash_x: {
                'FP_charge': Fraction(1, 1),
                'TP_charge': Fraction(0, 1)
            }
        }

    # trivial False Negatives
    trivial_FNs = r_join[r_join.geohash_x.isna()]
    for tup in trivial_FNs.itertuples():
        charges_dict = {
            **charges_dict,
            tup.geohash_y: {
                'FN_charge': Fraction(1, 1),
                'TP_charge': Fraction(0, 1)
            }
        }

    # less trivial cases
    groups = make_groups()
    for group in groups:
        group_assessment = assess_group(group)
        this_group_charges_dict = {}

        for el in group:
            if el.startswith(dets_prefix):
                this_group_charges_dict[el] = {
                    'TP_charge': Fraction(min(group_assessment['cnt_gt'], group_assessment['cnt_dets']), group_assessment['cnt_dets']),
                    'FP_charge': Fraction(group_assessment['FP_charge'], group_assessment['cnt_dets'])      
                }
        
            if el.startswith(gt_prefix):
                this_group_charges_dict[el] = {
                    'TP_charge': Fraction(min(group_assessment['cnt_gt'], group_assessment['cnt_dets']), group_assessment['cnt_gt']),
                    'FN_charge': Fraction(group_assessment['FN_charge'], group_assessment['cnt_gt'])
                }
        
        charges_dict = {**charges_dict, **this_group_charges_dict}
    
    _gt = _gt.apply(lambda row: assign_groups(row), axis=1)
    _dets = _dets.apply(lambda row: assign_groups(row), axis=1)

    _gt = _gt.apply(lambda row: assign_charges(row), axis=1)
    _dets = _dets.apply(lambda row: assign_charges(row), axis=1)

    return _gt[gt.columns.to_list() + ['group_id', 'TP_charge', 'FN_charge']], _dets[dets.columns.to_list() + ['group_id', 'TP_charge', 'FP_charge']]


def precision_recall_f1( tp, fp, fn ):

    p = 0. if tp == 0.0 else 1.*tp/(tp+fp)
    r = 0. if tp == 0.0 else 1.*tp/(tp+fn)
    f1 = 0. if p == 0.0 or r == 0.0 else 2.*p*r/(p+r)

    return dict(p=p, r=r, f1=f1)


def legacy_assess(tagged_gt, tagged_dets):

    #tmp_gdf = tagged_gt[tagged_gt.sector == sector].copy()
    tmp1 = tagged_gt.tag.value_counts().to_dict()
    tp = tmp1.get('TP', 0)
    fn = tmp1.get('FN', 0)

    tmp2 = tagged_dets.tag.value_counts().to_dict()
    _tp = tmp2.get('TP', 0)
    
    try:
        assert _tp == tp, f"{_tp} != {tp}"
    except AssertionError as e:
        print(f"AssertionError: {e}")
    fp = tmp2['FP']

    metrics = precision_recall_f1(tp, fp, fn)

    output = OrderedDict(
        TP=tp,
        FP=fp,
        FN=fn,
        p=metrics['p'],
        r=metrics['r'],
        f1=metrics['f1']
    )

    output['TP+FN'] = tp+fn
    output['TP+FP'] = tp+fp

    return output

def assess(tagged_gt, tagged_dets):

    assert 'TP_charge' in tagged_dets.columns.tolist()
    assert 'TP_charge' in tagged_gt.columns.tolist()
    assert 'FP_charge' in tagged_dets.columns.tolist()
    assert 'FN_charge' in tagged_gt.columns.tolist()
    
    TP = float(tagged_dets.TP_charge.sum())
    FP = float(tagged_dets.FP_charge.sum())

    _TP = float(tagged_gt.TP_charge.sum()) # x-check
    FN = float(tagged_gt.FN_charge.sum())
    
    try:
        assert _TP == TP, f"{_TP} != {TP}"
    except AssertionError as e:
        print(f"AssertionError: {e}")

    metrics = precision_recall_f1(TP, FP, FN)

    output = OrderedDict(
        TP=TP,
        FP=FP,
        FN=FN,
        p=metrics['p'],
        r=metrics['r'],
        f1=metrics['f1']
    )

    output['TP+FN'] = TP+FN
    output['TP+FP'] = TP+FP

    return output