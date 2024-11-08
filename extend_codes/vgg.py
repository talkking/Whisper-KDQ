# import torch
# import torch.nn as nn
# import torch.nn.functional as F

# class VGG2L(nn.Module):
#     def __init__(self, in_channel=1, out_channel=128, bn=True, keepbn=False):
#         super().__init__()
#         sc = out_channel // 2 # small channel
#         oc = out_channel # output channel
#         self.conv = nn.ModuleList([
#                         nn.Conv2d(in_channel, sc, 3, stride=1, padding=1),
#                         nn.Conv2d(sc, sc, 3, stride=1, padding=1),
#                         nn.Conv2d(sc, oc, 3, stride=1, padding=1),
#                         nn.Conv2d(oc, oc, 3, stride=1, padding=1),
#                         ])
#         self.norm = nn.ModuleList([
#                         nn.BatchNorm2d(sc),
#                         nn.BatchNorm2d(sc),
#                         nn.BatchNorm2d(oc),
#                         nn.BatchNorm2d(oc),
#                         ]) if bn == True else None
#         self.in_channel = in_channel
#         self.outdim = lambda x: ((x // in_channel - 1) // 4 + 1) * oc
#         self.keepbn = keepbn

#     def forward(self, xs, length):
#         xs = xs.view(xs.size(0), xs.size(1), self.in_channel, xs.size(2) // self.in_channel)
#         xs = xs.transpose(1, 2).contiguous()

#         if self.keepbn:
#             for i in range(len(self.norm)):
#                 self.norm[i].eval()

#         for i in range(2):
#             mask = torch.ones(xs.size(0), xs.size(2)).cuda()
#             for j in range(xs.size(0)):
#                 mask[j,length[j]:]=0
#             mask = mask.view(xs.size(0), 1, xs.size(2), 1)

#             for j in range(2):
#                 xs = xs * mask
#                 xs = self.conv[i*2+j](xs)
#                 if self.norm is not None:
#                     xs = self.norm[i*2+j](xs)
#                 xs = F.relu( xs, inplace=True )
            
#             xs = xs * mask
#             xs = F.max_pool2d(xs, 2, stride=2, ceil_mode=True)
#             length = ( length - 1 ) // 2 + 1

#         xs = xs.transpose(1, 2).contiguous()
#         xs = xs.view(xs.size(0), xs.size(1), -1)
#         return xs, length


import torch
import torch.nn as nn
import torch.nn.functional as F

class VGG2L(nn.Module):
    def __init__(self, in_channel=1, out_channel=128, bn=True, keepbn=False):
        super().__init__()
        sc = out_channel // 2 # small channel
        oc = out_channel # output channel
        self.conv = nn.ModuleList([
                        nn.Conv2d(in_channel, sc, 3, stride=1, padding=1), 
                        #nn.Conv2d(sc, sc, 3, stride=1, padding=1),
                        nn.Conv2d(sc, oc, 3, stride=1, padding=1),
                        #nn.Conv2d(oc, oc, 3, stride=1, padding=1),
                        ])
        self.norm = nn.ModuleList([
                        nn.BatchNorm2d(sc),
                        #nn.BatchNorm2d(sc),
                        nn.BatchNorm2d(oc),
                        #nn.BatchNorm2d(oc),
                        ]) if bn == True else None
        self.in_channel = in_channel
        self.outdim = lambda x: ((x // in_channel - 1) // 4 + 1) * oc * 2
        self.keepbn = keepbn

    def forward(self, xs, length): #xs:[B, T, D] length: [B]
        xs = xs.view(xs.size(0), xs.size(1), self.in_channel, xs.size(2) // self.in_channel) # [B, T, C, D]
        xs = xs.transpose(1, 2).contiguous()  #[B, C, T, D]

        if self.keepbn:
            for i in range(len(self.norm)):
                self.norm[i].eval()

        #for i in range(2):
        mask = torch.ones(xs.size(0), xs.size(2)).to(xs.device) # mask: [B, T]=1
        for j in range(xs.size(0)):
            mask[j,length[j]:]=0    
        mask = mask.view(xs.size(0), 1, xs.size(2), 1)  #mask: [B, 1, T, 1]

        for j in range(2):
            xs = xs * mask    
            xs = self.conv[j](xs)
            if self.norm is not None:
                xs = self.norm[j](xs)
            xs = F.relu( xs, inplace=True )
        
        xs = xs * mask
        xs = F.max_pool2d(xs, 2, stride=2, ceil_mode=True) # [B, C, T/2, D]
        length = ( length - 1 ) // 2 + 1

        xs = xs.transpose(1, 2).contiguous() #[B, T, C, D]
        xs = xs.view(xs.size(0), xs.size(1), -1) #[B, T, D]
        return xs, length
