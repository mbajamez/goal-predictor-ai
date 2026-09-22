import numpy as np
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import brier_score_loss, log_loss

class ProbabilityCalibrator:
    def __init__(self):
        self.model = IsotonicRegression(y_min=1e-4,y_max=1-1e-4,out_of_bounds="clip")
        self.fitted=False

    def fit(self,p,y):
        p=np.asarray(p,float); y=np.asarray(y,int)
        if len(np.unique(y)) < 2:
            return self
        self.model.fit(p,y); self.fitted=True
        return self

    def transform(self,p):
        p=np.asarray(p,float)
        return self.model.predict(p) if self.fitted else np.clip(p,1e-4,1-1e-4)

def calibration_error(p,y,bins=10):
    p=np.asarray(p); y=np.asarray(y)
    edges=np.linspace(0,1,bins+1)
    e=0.0; n=len(y)
    for lo,hi in zip(edges[:-1],edges[1:]):
        mask=(p>=lo)&(p<hi if hi<1 else p<=hi)
        if mask.any():
            e += mask.sum()/n * abs(p[mask].mean()-y[mask].mean())
    return float(e)

def metrics(p,y):
    p=np.clip(np.asarray(p),1e-6,1-1e-6)
    y=np.asarray(y)
    return {
        "brier":float(brier_score_loss(y,p)),
        "log_loss":float(log_loss(y,p,labels=[0,1])),
        "calibration_error":calibration_error(p,y),
        "accuracy_50":float(((p>=0.5)==(y==1)).mean())
    }
