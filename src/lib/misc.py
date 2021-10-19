import numpy as np
import pygeohash as pgh
import pandas as pd
import geopandas as gpd

from collections import OrderedDict
from scipy.spatial import cKDTree


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
        tmp = gpd.clip(gdf, sector.geometry)
        tmp['sector'] = sector.sector
        clipped_gdf = pd.concat([clipped_gdf, tmp])

    return clipped_gdf


def tag(gt, preds, tol):

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


def precision_recall_f1( tp, fp, fn ):

    p = 0. if tp == 0.0 else 1.*tp/(tp+fp)
    r = 0. if tp == 0.0 else 1.*tp/(tp+fn)
    f1 = 0. if p == 0.0 or r == 0.0 else 2.*p*r/(p+r)

    return dict(p=p, r=r, f1=f1)


def assess(tagged_gt, tagged_preds):

    #tmp_gdf = tagged_gt[tagged_gt.sector == sector].copy()
    tmp1 = tagged_gt.tag.value_counts().to_dict()
    tp = tmp1.get('TP', 0)
    fn = tmp1.get('FN', 0)

    tmp2 = tagged_preds.tag.value_counts().to_dict()
    _tp = tmp2.get('TP', 0)
    
    try:
        assert _tp == tp, f"{_tp} != {tp}"
    except AssertionError as e:
        print(f"AssertionError: {e}")
    fp = tmp2['FP']

    tmp3 = precision_recall_f1(tp, fp, fn)

    output = OrderedDict(
        TP=tp,
        FP=fp,
        FN=fn,
        p=tmp3['p'],
        r=tmp3['r'],
        f1=tmp3['f1']
    )

    output['TP+FN'] = tp+fn
    output['TP+FP'] = tp+fp

    return output