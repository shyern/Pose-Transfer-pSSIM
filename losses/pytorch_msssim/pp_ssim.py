import torch
import torch.nn.functional as F
from .ssim import _fspecial_gauss_1d, ssim

def bp_ssim(X, Y, bp_mask, mask_t=0.4, data_range=255, size_average=True, K=(0.01,0.03)):
    batch_size, img_channel, H, W = X.shape[0], X.shape[1], X.shape[2], X.shape[3]
    mask_channel = bp_mask.shape[1]
    new_shape = (batch_size, img_channel*mask_channel, H, W)

    X_repeat = torch.unsqueeze(X, 1).repeat(1, mask_channel, 1, 1, 1).reshape(new_shape)
    Y_repeat = torch.unsqueeze(Y, 1).repeat(1, mask_channel, 1, 1, 1).reshape(new_shape)
    bp_mask_repeat = torch.unsqueeze(bp_mask, 2).repeat(1,1,img_channel,1,1).reshape(new_shape)

    K1, K2 = K
    compensation = 1.0

    C1 = (K1 * data_range) ** 2
    C2 = (K2 * data_range) ** 2

    # calculate mean of X and Y (method 1)
    bp_mask_sum = torch.unsqueeze(torch.unsqueeze(bp_mask_repeat.sum((-2,-1)),-1),-1).repeat(1,1,H,W)
    bp_mask_avg = bp_mask_repeat/(bp_mask_sum + 1e-6) # sum(bp_mask[0,0,:,:]) = 1
    mu1 = torch.mul(X_repeat, bp_mask_avg).sum((-2,-1))
    mu2 = torch.mul(Y_repeat, bp_mask_avg).sum((-2,-1))

    # # calculate mean of X and Y (method 2)
    # no_zero_count = torch.sum(bp_mask>mask_t)
    # mu1 = torch.mul(X, bp_mask).sum()/no_zero_count
    # mu2 = torch.mul(Y, bp_mask).sum()/no_zero_count

    mu1_sq = mu1.pow(2)
    mu2_sq = mu2.pow(2)
    mu1_mu2 = mu1 * mu2

    mu11 = torch.mul(X_repeat*X_repeat, bp_mask_avg).sum((-2,-1))
    mu22 = torch.mul(Y_repeat*Y_repeat, bp_mask_avg).sum((-2,-1))
    mu12 = torch.mul(X_repeat*Y_repeat, bp_mask_avg).sum((-2,-1))
    sigma1_sq = compensation * (mu11 - mu1_sq)
    sigma2_sq = compensation * (mu22 - mu2_sq)
    sigma12   = compensation * (mu12 - mu1_mu2)

    cs = (2 * sigma12 + C2) / (sigma1_sq + sigma2_sq + C2) # set alpha=beta=gamma=1
    ssim = ((2 * mu1_mu2 + C1) / (mu1_sq + mu2_sq + C1)) * cs

    if size_average:
        ssim_avg = ssim.mean()
    else:
        ssim_avg = ssim.mean(-1)

    return ssim_avg

def ms_bp_ssim(X, Y, bp_mask, data_range=255, size_average=True, K=(0.01,0.03), nonnegative_ssim=True):
    batch_size, img_channel, H, W = X.shape[0], X.shape[1], X.shape[2], X.shape[3]
    scale_channel, mask_channel = bp_mask.shape[1], bp_mask.shape[2]
    new_shape = (batch_size, scale_channel, img_channel*mask_channel, H, W)

    weights = torch.FloatTensor(
        [0.0448, 0.2856, 0.3001, 0.2363, 0.1333]).to(X.device, dtype=X.dtype)
    # [0.0448, 0.2856, 0.3001, 0.2363, 0.1333]

    X_repeat = torch.unsqueeze(torch.unsqueeze(X, 1),1).repeat(1, scale_channel, mask_channel, 1, 1, 1).reshape(new_shape)
    Y_repeat = torch.unsqueeze(torch.unsqueeze(Y, 1),1).repeat(1, scale_channel, mask_channel, 1, 1, 1).reshape(new_shape)
    bp_mask_repeat = torch.unsqueeze(bp_mask, 3).repeat(1,1,1,img_channel,1,1).reshape(new_shape)

    K1, K2 = K
    compensation = 1.0

    C1 = (K1 * data_range) ** 2
    C2 = (K2 * data_range) ** 2

    # calculate mean of X and Y (method 1)
    bp_mask_sum = torch.unsqueeze(torch.unsqueeze(bp_mask_repeat.sum((-2,-1)),-1),-1).repeat(1,1,1,H,W)
    bp_mask_avg = bp_mask_repeat/(bp_mask_sum + 1e-6) # sum(bp_mask[0,0,:,:]) = 1
    mu1 = torch.mul(X_repeat, bp_mask_avg).sum((-2,-1))
    mu2 = torch.mul(Y_repeat, bp_mask_avg).sum((-2,-1))

    # # calculate mean of X and Y (method 2)
    # no_zero_count = torch.sum(bp_mask>mask_t)
    # mu1 = torch.mul(X, bp_mask).sum()/no_zero_count
    # mu2 = torch.mul(Y, bp_mask).sum()/no_zero_count

    mu1_sq = mu1.pow(2)
    mu2_sq = mu2.pow(2)
    mu1_mu2 = mu1 * mu2

    mu11 = torch.mul(X_repeat*X_repeat, bp_mask_avg).sum((-2,-1))
    mu22 = torch.mul(Y_repeat*Y_repeat, bp_mask_avg).sum((-2,-1))
    mu12 = torch.mul(X_repeat*Y_repeat, bp_mask_avg).sum((-2,-1))
    sigma1_sq = compensation * (mu11 - mu1_sq)
    sigma2_sq = compensation * (mu22 - mu2_sq)
    sigma12   = compensation * (mu12 - mu1_mu2)

    cs = (2 * sigma12 + C2) / (sigma1_sq + sigma2_sq + C2) # set alpha=beta=gamma=1
    ssim = ((2 * mu1_mu2 + C1) / (mu1_sq + mu2_sq + C1)) * cs

    if nonnegative_ssim:
        ssim = F.relu(ssim, inplace=False)
        cs = F.relu(cs, inplace=False)

    cs_batch = torch.mean(cs, -1)
    ssim_batch = torch.mean(ssim, -1)

    msssim = torch.prod(cs_batch[:,:-1], dim=1)*ssim_batch[:,-1]
    # msssim = torch.prod((cs_batch[:,:-1]**weights[:-1].unsqueeze(0)),dim=1)*(ssim_batch[:,-1]**weights[-1])
    # top[0].data[...] = 1 - np.sum(self.l[-1, :, :, :, :] * self.Pcs) / (bottom[0].channels * bottom[0].num)
    # msssim_val = torch.prod((mcs[:-1] ** weights[:-1].unsqueeze(1)), dim=0) * (ssim_val ** weights[-1]) # (batch, )

    if size_average:
        ssim_avg = msssim.mean()
    else:
        ssim_avg = msssim.mean(-1)

    return ssim_avg

class Part_SSIM(torch.nn.Module):
    def __init__(self, data_range=None, size_average=True, K=(0.01, 0.03)):
        r""" class for bp-ssim
        Args:
            win_size: (int, optional): the size of gauss kernel
            win_sigma: (float, optional): sigma of normal distribution
            data_range (float or int, optional): value range of input images. (usually 1.0 or 255)
            size_average (bool, optional): if size_average=True, ssim of all images will be averaged as a scalar
            channel (int, optional): input channels (default: 3)
            weights (list, optional): weights for different levels
            K (list or tuple, optional): scalar constants (K1, K2). Try a larger K2 constant (e.g. 0.4) if you get a negative or NaN results.
            nonnegative_ssim (bool, optional): force the ssim response to be nonnegative to avoid NaN results.
        """

        super(Part_SSIM, self).__init__()
        self.data_range = data_range
        self.size_average = size_average

    def forward(self, X, Y, bp_mask_):
        # from [-1,1] to [0,1]
        X = (X + 1) / 2.0
        Y = (Y + 1) / 2.0
        bp_mask = bp_mask_[:,1:,:,:]

        ssim = bp_ssim(X, Y, bp_mask, data_range=self.data_range, size_average=self.size_average)

        # mask_channel = bp_mask.shape(1)
        # ssim_all = [bp_ssim(X, Y, bp_mask[:,i,:,:]) for i in range(mask_channel)]
        # ssim = ssim_all.mean()

        return ssim

class MS_Part_SSIM(torch.nn.Module):
    def __init__(self, data_range=None, size_average=True, K=(0.01, 0.03)):
        r""" class for bp-ssim
        Args:
            win_size: (int, optional): the size of gauss kernel
            win_sigma: (float, optional): sigma of normal distribution
            data_range (float or int, optional): value range of input images. (usually 1.0 or 255)
            size_average (bool, optional): if size_average=True, ssim of all images will be averaged as a scalar
            channel (int, optional): input channels (default: 3)
            weights (list, optional): weights for different levels
            K (list or tuple, optional): scalar constants (K1, K2). Try a larger K2 constant (e.g. 0.4) if you get a negative or NaN results.
            nonnegative_ssim (bool, optional): force the ssim response to be nonnegative to avoid NaN results.
        """

        super(MS_Part_SSIM, self).__init__()
        self.data_range = data_range
        self.size_average = size_average

    def forward(self, X, Y, bp_mask):
        # from [-1,1] to [0,1]
        X = (X + 1) / 2.0
        Y = (Y + 1) / 2.0

        ssim = ms_bp_ssim(X, Y, bp_mask, data_range=self.data_range, size_average=self.size_average)

        # mask_channel = bp_mask.shape(1)
        # ssim_all = [bp_ssim(X, Y, bp_mask[:,i,:,:]) for i in range(mask_channel)]
        # ssim = ssim_all.mean()

        return ssim

class P_plus_P_SSIM(torch.nn.Module):
    def __init__(self, win_size=11, win_sigma=1.5, data_range=None, size_average=True, channel=3, K=(0.01, 0.03), nonnegative_ssim=False):
        r""" class for bp-ssim
        Args:
            win_size: (int, optional): the size of gauss kernel
            win_sigma: (float, optional): sigma of normal distribution
            data_range (float or int, optional): value range of input images. (usually 1.0 or 255)
            size_average (bool, optional): if size_average=True, ssim of all images will be averaged as a scalar
            channel (int, optional): input channels (default: 3)
            weights (list, optional): weights for different levels
            K (list or tuple, optional): scalar constants (K1, K2). Try a larger K2 constant (e.g. 0.4) if you get a negative or NaN results.
            nonnegative_ssim (bool, optional): force the ssim response to be nonnegative to avoid NaN results.
        """

        super(P_plus_P_SSIM, self).__init__()
        self.win = _fspecial_gauss_1d(
            win_size, win_sigma).repeat(channel, 1, 1, 1)
        self.win_size = win_size
        self.win_sigma = win_sigma
        self.size_average = size_average
        self.data_range = data_range
        self.K = K
        self.nonnegative_ssim = nonnegative_ssim
        self.channel = channel

    def forward(self, X, Y, bp_mask_):
        # from [-1,1] to [0,1]
        X = (X + 1) / 2.0
        Y = (Y + 1) / 2.0
        f_mask = bp_mask_[:,2:,:,:]

        f_ssim = bp_ssim(X, Y, f_mask, data_range=self.data_range, size_average=self.size_average)

        b_mask = torch.unsqueeze(bp_mask_[:,1,:,:], 1).repeat(1, self.channel, 1, 1)
        bX = torch.mul(b_mask, X)
        bY = torch.mul(b_mask, Y)
        b_ssim = ssim(bX, bY, win_size=self.win_size, win_sigma=self.win_sigma, win=self.win, data_range=self.data_range,
             size_average=self.size_average, K=self.K, nonnegative_ssim=self.nonnegative_ssim)

        # all_ssim = ssim(X, Y, win_size=self.win_size, win_sigma=self.win_sigma, win=self.win,
        #               data_range=self.data_range,
        #               size_average=self.size_average, K=self.K, nonnegative_ssim=self.nonnegative_ssim)

        return (f_ssim+b_ssim)/2